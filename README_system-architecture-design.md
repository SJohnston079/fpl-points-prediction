# **FPL Prediction System: Production Architecture Design**

## **1\. System Philosophy**

This system is a **Rules-Agnostic Data Lakehouse**. It treats FPL points as a "Synthetic Label" derived from immutable raw match statistics. This allows the model to be retrained on historical data using modern or experimental scoring rules.

### **Core Principles**

* **Stat-First Modeling**: We model the relationship between raw Opta-style stats and points.  
* **Target Normalization**: Historical performance is re-scored using current rules to ensure a consistent training target.  
* **Hash-Based Recomputation**: The system automatically detects rule changes via config hashes and triggers historical re-scoring.

## **2\. Directory Structure**

fpl-forecaster/  
├── configs/  
│   ├── scoring\_rules.yaml    \# Points per goal, assist, recovery, etc.  
│   └── pipeline\_state.json   \# Tracks the hash of scoring\_rules.yaml  
├── data/  
│   ├── 00\_raw/               \# Immutable snapshots (JSON/CSV)  
│   ├── 01\_ingested/          \# Standardized Parquet (Raw atoms: tackles, passes)  
│   ├── 02\_labels/            \# Synthesized points based on scoring\_rules.yaml  
│   ├── 03\_features/          \# Calculated metrics (Lags, rolling averages, ELO)  
│   ├── 04\_feature\_store/     \# Final Join: Features \+ Synthetic Labels  
│   └── 05s\_evaluation/        \# \[Placeholder\] Model performance logs  
├── src/  
│   ├── synthesis/            \# Logic for Core Points and BPS Ranking  
│   ├── engineering/          \# Logic for calculating rolling features/lags  
│   └── store/                \# Logic for incremental vs full-refresh updates  
└── ...

## **3\. The Rules Synthesis Logic**

To handle new data and historical changes, the src/synthesis module operates in two modes:

### **A. Incremental Mode (New Data)**

1. **Detect**: Finds season/gw present in 02\_ingested but missing from 03\_labels.  
2. **Apply**: Runs the points engine on only those new rows.  
3. **Append**: Upserts the results into the Parquet store.

### **B. Full Re-compute Mode (Rule Change)**

1. **Trigger**: Triggered if hash(scoring\_rules.yaml) does not match the hash in pipeline\_state.json.  
2. **Purge**: Deletes 03\_labels/ and 05\_feature\_store/.  
3. **Re-run**: Processes every row in 02\_ingested from all available historical seasons.  
4. **Update**: Saves the new hash to pipeline\_state.json.

### **C. Bonus Point System (BPS) Logic**

The BPS is context-dependent and requires match-level grouping:

* **Match Grouping**: The engine groups 02\_ingested data by match\_id.  
* **BPS Scoring**: Every player receives a BPS score based on the 30+ metrics (Pass %, Big Chances Created, etc.) defined in the YAML.  
* **Ranking**: The engine ranks players *within* each match.  
* **Tie-Breaking**: Implements official FPL tie-break logic:  
  * *Tie for 1st*: Both get 3pts, next gets 1pt.  
  * *Tie for 2nd*: Top gets 3pts, next two get 2pts each.  
  * *Tie for 3rd*: Top gets 3pts, second gets 2pts, next two get 1pt each.

## **4\. Training & Evaluation**

### **Training Pipeline**

* **Two-Stage Approach**:  
  1. **Minutes Model**: Predicts the likelihood of playing 0, 1-60, or 60-90 minutes.  
  2. **Performance Model**: Predicts synth\_total\_points *given* 90 minutes of play.  
* **Target Variable**: The Performance model is trained on "Points per 90" (or points normalized by minutes) using the synth\_total\_points from Section 3\.

### **Evaluation**

* **Backtesting Strategy**: Time-series cross-validation (Walk-forward).  
* **Metrics**:  
  * **Minutes**: Accuracy/MAE on playtime.  
  * **Points**: Root Mean Squared Error (RMSE) on expected points (![][image1]).  
  * **Decision**: Precision@K for captaincy and transfer recommendations.

## **5\. Inference Workflow**

Inference is executed in a multi-step pipeline for each horizon (![][image2]):

1. **Feature Assembly**: Pulls latest player form and upcoming fixture FDR.  
2. **Minutes Prediction**: Estimates expected minutes (![][image3]) for each player.  
3. **Rate Prediction**: Predicts the point-scoring rate (![][image4]) based on opponent strength and player stats.  
4. **Expected Points Calculation**:  
   ![][image5]  
5. **Multi-Horizon Aggregation**: Sums ![][image6] across the rolling window to inform the optimization engine.

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADQAAAAZCAYAAAB+Sg0DAAADaklEQVR4Xu1Wz2sTQRTekAqKihatpU26m6RgKAgqOajQmwXbg57Eg/0DxFI8WNCb9iKIIIieFEE9iEVELVKUHkRQUBFEhKIHD1UKxUMpCBW0tPX7svOS13E3E0zSi/ngY368ee/Nt/N2dj2vif8AmUxmfRAEHd3d3TswTNr2RoD5yFQqtQ3DhG2vCb7vH0bwGxB2Edxq2xsB5gMfId9kW1vbJtteBIx7zEInuVb8KEjHWSsgbwF8HCsom80GWHAUPIdNr4BXzbhIjIcgZBztEsa94lcHQUnE7LAnXXAKElAIOMF3w7YRDKQ3UKOgBPxvdXV1HbENLlQlCAtasdl3aM/qeczt9czLx0D5fH6z2GoRJPnAHtvmQlWCUHa7EfwHFvbpeT5FTwlC06Jsfwni7aMT8bKIupHMaS+k0+kNet5CIuoGrUoQgg/y/UGClMzRARs6oddp2IIKhcI6xJgCf4MjeEh5tO/BL4jzkacBfmceiwvmYQkSWH8S83OYf2t8BsToFNTZ2bk9CDey4quLAPyMfqu9XmAJasEm7nB9EJbSAsb7xEgb47Ov8s2U3UOIP9oxDJPw6zeieVUX322nIC7gBsCf1jzfp1Kp5HK5Lcq8SlB7e/tG+A+rWC9UwhaMH4ggrOlFfxGcEH9BEH44v4JL4DXGZdnpi8opiGVlnsKUNX9F+rBlwVfabp1QESrWBZnTFcAx2tPsmwe2CqZs75sYJMt3yFMP1iWo9PT88AKIBOzDWiARJYgxzEZ0zcuJzHnlfIucV64l8FRgO+WH7w9j/QIPiL2iIF4CWDxtHAdtOwEhGdje4JuxS89HCQrCk5iFLSdzcB818e+pfNPsmxM5bm7C4rcQvgfFF/3b9NW5KgrC4ksm2QcJSrBm+QcRhPW8jHG/9iNiBDHWvIgPwl+med98DtgyHtrzHCPuOPOwb07mGfaRVvE+Ye6M5yo5+e6YDbioX/ASIgSxnJbBm+AMeBd8jctkpyzgxYK5p+As+DCj/g2JIHyAvCX5IJ6DIzxFvSZSUD1gC5JyYssTDuL/0xKsBvPRtFG00TfGvnaCTDnF/gvWCw0XBBE9EHGdZYR2Eu3lCqdTMxoqiBuHiP3oH/PLfxkDjn+0f4bJdwjtk0YI6gO/IfjLuHqvN5jPcIy3om1vook1wh+usy6bkjc+bAAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACkAAAAZCAYAAACsGgdbAAACtUlEQVR4Xu2VO2hUQRSGd8n6QsUgxiX7uvuSxVVRWQwoFhYpDKKIJFhYikiwEIIoKFZip42oRViJIikUQUGCSLYQYpHSJliIYCRgpVYRomj8/txzZRjExr2wxf7wM49z7px/zpmZm0h00UUHIwiC7fAunC0UCh9p7xWLxV7fL0K5XN6E/YH5voG3GRd9v7Yik8lsIcZxgp4n4DL8LOG+nyGJ7QL8Ll++GaY9kk6n1/uOsYBgl+GkBT/q2wVs49hGaBfhgm+PFWRyLUGfw1sm8pLvA5ISiO9Z+cAp3yFWZLPZHEFn4ZgJaPo+pVJpoFqtrkHoxD82Eh8IOEjgpypzlCVlN7L39fVtwHZf5xfbHPzB+KC7RqywUkvgICzT/wQXlF3ZmduhzOZyuXVOpp9gSnlLxQcTNoOIrJOpReYbJqwpofKVOInUufTXiRX5fP4YgR/TTekpod+SEJVeYlxBzH+A3/hmn7NE/AjCGz0WjfVQW0lV2oc6j47vLzinjEdzsaNWq20kYy/dS6BbayJvwL2uv2V4gm7SnY8TPWTtEYHfU76dCQtsN10Zazm+SXz3MLcke+SrlvFF5qf1u9QE/XNq8R/V5m3Tb3nCdiuW/Givcd630c5rDdp++M7WDhGE/2v9/pYdvnZsWnSgXq+v5sNnnl/EIbgfLsHTsB9hhwm+y16ME9bqOE2ydIr2QKVS2cr8IUuGRCqmRM5rQ39EtgtBeG6/svgZOFywV8DzmfnbaxCEv+GVv5Yybpsd8v3+G1bKGZ1t34awXl26IDxOK69BdOEsw1PwusbOkUi7a7QFjUZjFYvfgU14Sq3eVpU0CJ+yqybmCryp46DvrNRf4DR8wfzJRNyXURmTMLo90Zw2gODNdJNqNY5sQVjqlirgzncM/FJ3JBA3Dn/CV5R9xLd30W78BubBzuLpgyWyAAAAAElFTkSuQmCC>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAZCAYAAABU+vysAAACLElEQVR4Xu2WP2gUQRTGNxhBMcGIHIfc3u7dETzSaLFYBCwtDKKVnSkCKQRBEEJiF2xC2iBIQM/CIkVIEQuttEgVi6sDNkEiQroUgRQ2xt+Xe2N2h5BwxwSb++Axs+/NzPvee/Nno6iPPrpAmqYTtVrtA+33JEl+Ih/pv3XSaDRuMmzAnxccOBvD+WPaFWQHUlP6Nt00coisQeiqPzc4SqXSEM42kCe+DUIvjcx2vV4v+/agwFkDR7s4uu3bLFMi0mbcNd8eFNVq9ZGcneQI/S8jMuPbggMnC3Lm67Msu2gEl9X37UHhyoL8To9PyyfLwhd//LnBlQVp5/UQnJT+3DPh4MqCtPJ6iGToDpAbef1ZYPxW16crd2xFpHB0IXIP3Z8eiHzmLrrk609Fbn/s+0fXZaqb6EQAeeXrzwSO3lk21vJRqK/IZFPW4ji+jG5V5YLYrbRzt3zVbWvPw2vNUxYrlUp87OHIx3iz2RxmL96h/6MQsD6UBSPxTzANujEsehfdAe1z2hYyKzvOE/pbqZXSiGxYmRf8sjD/ITIvnwQ0GvXybhHd9aTz7mR8XpDOIttGxvRN2xZRl8XCAtHRGrELlHXmol6InAQcPpVzdwvT30N33/bbjnQqn8qplxvbi3K5fAX7ostcccUeYWXZVBlYfFlOpLfIvyFv3EtN/wGyDpkl2vdBX3BFrXqz+IgfnV1+hdRL5++bIMiX5X9hABLPks5f3LwrSR8h8Re+l6ABcFwRBQAAAABJRU5ErkJggg==>

[image5]: <data:image/png;base64,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>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFUAAAAZCAYAAABAb2JNAAAE40lEQVR4Xu2YS2hcVRjHZ0iFis+qMTaPOTNJMAg+GWypFBQMYhe6UBeVunMhlIpSUHdakIK6KhIRilLEhUVFFI1VKBJUNNCNiiFFFGKp7UKKEEyhlUZ//7nfGb4c781ciVGazh8+zrnf65zzP8+ZSqWLLi4Y1Ov19SGEjSMjI9fy2ZPa1yKazeZFGnOj0ehTPbWvGLVa7T4a2A+5LyBXpva1CMZZZ9wHKH6gbKb2NnC4VeSUEfnGOJHq80T09vZeiu05i/mJ+jHK6STXowMDA1ensWWhXfJ/TaSN7/1lSWUpBxweQp5lsH8iL9t3S/jeyQA+oDzH99YYV0SqtgW2u5FHlE+xMRf17UbqWWQhjS0DJmOQ2Fn1h3x3pfZ/gCpjvyVVdkIpUiNEJjKpVZDaBCXBvtF955IaoQnA/xRyQ45NuRY65SjC8PDwFSs902j7GU16qu+E0qTisIEGjqghr0d3G0XVfJpjY2OXRVsnQojdjUypEzm2HRoQsi21/UdYR9vvIoupoRNKk6ptQAPzOI57Pd8HKo5UinXOthypsdN7UwOoKq9I1S2aGgV1vOiGtbO41SeHqvR+AhVblH9wcHCA9ueQ2dTmoXM77UNpUuPKUWNRp2CSPub9PJYj1XX6byuRgW5C/xtyLrWR83H0J5DvaftzytN9fX2XmLkH+xPofkcO6QiQ0p45E8hXyFntJmL3Uf8FOU7Mwegr4jXOVNKxoNsWrB8hO8J2VmwiS5Ha399/DUEzlrx9OSFHqW9I/SPSjnjU7LwK2aCOSayTc9SfHh0dvdz7a9DYDkPGZq8XQRqUTcRHQ0NDNxL/CfUzyBb5UL6Dbqsbx4M+h42rfazpzkA3iZwm3+3eVwjZDvs6TkTIFsC38bVSilQZCVpQI4leHWlvs9hIRBGprtNlL4Eqvs+b/5JtbaT+YRO9y3KfEbHshovlo0nSNhWx8o36COX1Ow6/YXQnkRlNhPcV0E8pBnkL3/H0WClFqhq0JDOJfl+sY2sgX3p7Eamu06VItdzHQ86lYbn0SmgPQHnzjqU4Dq8TATnx2tpave37wiPYBEch74v+XC1DarxQYiO5CNkqaZMsFJEaO42cTG150GrAdxGZS21sz/vRz8YLR2XIJqCRuObe5nxvqblVbbq91r8d3jdCBDLWh7EfDtl7WsRuj/aOpLoLpbAREtaxTes88/plSI2dnkxteVAe859KTDoWJmh+T1RocNLJBsE3I/dI78YxF33Nfw+6XVa/U0SoneBWL/UHyBPM57qQ8RBXcI/6VnNnckdSCXjJBvSN/9lI8vVqCPyMLPJ9r48T8kjF946QHezKmTtJKbSK8P0QOeF0oyG7eY9EnW3lKa1W+rOZ+ptxBYbsTbzkWOAOuB7dr0aCft29UslW9Cm+D1LvIf4q8m2KMdhea7hfWbKj219q+ysQ53l1pITkPuA9qXr2hGy7pLG7fUwRbIW8R/kG5Wche8Y8lV462J9E/zEyHVeX6RW35OysZAROoPtUJMaLlvqrIXuWvY386PxbP9nBUeR1EUc57550LRSS+m8gb6WuFKHEX4l5dntT5/3B0vpRoNIr5asVnz7so039KLKfd6SeD+iSugpYdVLLbNe1BB0HdokeWi1Sx2vZz88vjNg1Dwi9SWPm3P1O9dTeRRddXJD4C83Mtj9cPxB5AAAAAElFTkSuQmCC>