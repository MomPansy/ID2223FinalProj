import json
import torch
import torch.nn as nn
import nltk
import joblib
from nltk.tokenize import word_tokenize
import hopsworks 
import gradio as gr

# Download NLTK punkt tokenizer
nltk.download('punkt')

class LSTMClassifier(nn.Module):
    """
    LSTM Classifier for text classification.
    """
    def __init__(self, embedding_matrix, hidden_dim, num_layers, num_classes, dropout=0.5):
        super(LSTMClassifier, self).__init__()
        vocab_size, embed_dim = embedding_matrix.shape

        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.embedding.weight = nn.Parameter(embedding_matrix)
        self.embedding.weight.requires_grad = False

        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers, dropout=dropout, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        x = self.embedding(x)
        lstm_out, _ = self.lstm(x)
        x = lstm_out[:, -1, :]
        return self.fc(x)

class Tokenizer:
    """
    Tokenizer for converting text to token indices.
    """
    def __init__(self, tokenizer, indices):
        self.tokenizer = tokenizer
        self.indices = indices

    def tokenize(self, text):
        return [self.indices.get(word, self.indices['<UNK>']) for word in self.tokenizer(text)]

def preprocess_input(user_input, tokenizer, max_length):
    """
    Preprocess user input text.
    """
    token_indices = tokenizer.tokenize(user_input)
    padded_indices = token_indices[:max_length] + [0] * (max_length - len(token_indices))
    return torch.tensor(padded_indices).unsqueeze(0)

def predict(user_input, model, tokenizer, max_length):
    """
    Make a prediction based on user input text.
    """
    model.eval()
    with torch.no_grad():
        preprocessed_input = preprocess_input(user_input, tokenizer, max_length)
        output = model(preprocessed_input)
        # Logic to interpret the output
        _, prediction = torch.max(output.data, 1)  # Implement based on model's output structure
    return prediction

def app(inputs):

    project = hopsworks.login() 
    fs = project.get_feature_store() 
    mr = project.get_model_registry()
    lstm_model = joblib.load(mr.get_model("lstm_model", version=1).download() + "/lstm.pkl")

    # Load tokenizer indices
    with open('indices.json', 'r') as file:
        indices = json.load(file)

    # Define tokenizer and max length
    tokenizer = Tokenizer(word_tokenize, indices)
    max_length = 100  # Define as per your model's training

    result = predict(inputs, lstm_model, tokenizer, max_length).item()
    label_encoding = {
        0: "True", 
        1: "False", 
        2: "Partially True"
    }
    return label_encoding[result]

demo = gr.Interface( 
    fn = app, 
    title = "Politifact Sentiment Analysis", 
    description = 'Insert a statement that you would like to check the truthfulness of', 
    allow_flagging = 'never', 
    inputs = [
       gr.Textbox(
           placeholder='Insert politifact here',
           label = 'Meaningful label')
    ], 
    outputs = [
         gr.Textbox(label='Prediction'),
    ]
)

demo.launch(debug = True)
