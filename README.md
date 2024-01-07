# Project README: ID2223 - Political Fact Checker

## Overview
This project is the culmination of the course ID2223 - Scalable Machine Learning and Deep Learning. Our team has developed a political fact-checking tool leveraging an LSTM model trained on dynamic data. The project comprises four key components: backfilling pipeline, EDA and feature engineering pipeline, transformation and training pipeline, and deployment into Hugging Face Spaces.

## Technologies Used
- **Hopsworks**: For the feature store.
- **Modal**: For function scheduling and deployment.
- **Hugging Face Spaces and Gradio**: For UI deployment.

## Project Components

### 1. Backfilling Pipeline
- **Data Source**: Historical data was sourced from [PolitiFact](https://www.politifact.com/factchecks/list/), scraping 600 data points.
- **Process**: The data was uploaded to the Hopsworks feature store.

### 2. EDA and Feature Engineering Pipeline
- **Scheduling**: A scheduler was deployed on Modal to retrieve all data points from the page daily.
- **Data Storage**: The retrieved data was uploaded to the Hopsworks feature store.

### 3. Transformation and Training Pipeline
- **Data Transformation**: This included label standardization and encoding, text tokenization and indexing, and converting the data into PyTorch tensors.
- **Model Training**: We used GloVe embeddings with 2 LSTM layers. Post-training, the model was uploaded to the Hopsworks model registry.

### 4. Deployment
- **UI Interface**: A simple UI was created on [Hugging Face Spaces](https://huggingface.co/spaces/Mompansy/politifactchecker).

## Potential Improvements
- Implement logic to avoid duplicate data points in the feature store.
- Increase the historical data size to improve model training and performance.

## Evaluation
- The model showed inconsistent performance, indicated by large fluctuations in F1 scores, likely due to overfitting.
- Future improvements could focus on expanding the data set and refining the model to enhance accuracy.

