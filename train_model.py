# train_model.py
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, GlobalAveragePooling1D, Dropout, LSTM, Bidirectional
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.callbacks import EarlyStopping
import numpy as np
import pickle
import pandas as pd


import numpy as np
import pickle

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

df = df.rename(columns={"spam": "is_spam"})

df['label'] = 0

import re

urgent_keywords = [
    "urgent", "asap", "immediately", "right away", "emergency",
    "deadline", "today", "now", "action required", "within the hour"
]

reply_keywords = [
    "please", "can you", "could you", "would you", "let me know",
    "confirm", "review", "approve", "rsvp", "respond", "reply",
    "schedule", "meeting", "call", "available", "feedback", "update"
]

combined_keywords = urgent_keywords + reply_keywords

def keyword_hit_count(text: str, keywords: list[str]) -> int:
    t = text.lower()
    hits = 0
    for kw in keywords:
        # count occurrences of keyword/phrase
        hits += len(re.findall(re.escape(kw), t))
    return hits

def assign_label(row):
    text = row["text"]
    
    # spam -> 0
    if row["is_spam"] == 1:
        return 0

    hits = keyword_hit_count(text, combined_keywords)
    
    # urgent if lots of signals
    if hits >= 6:
        return 2
    
    else:
        return 1

df["label"] = df.apply(assign_label, axis=1)

# Build X/y from your dataframe
texts = df["text"].astype(str).tolist()
labels = df["label"].astype(int).tolist()


X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.4, random_state=42, stratify=labels
)

#tokenize
MAX_WORDS = 20000
MAX_LEN = 100

tokenizer = Tokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
tokenizer.fit_on_texts(X_train)

train_seq = tokenizer.texts_to_sequences(X_train)
test_seq  = tokenizer.texts_to_sequences(X_test)

X_train_pad = pad_sequences(train_seq, maxlen=MAX_LEN)
X_test_pad  = pad_sequences(test_seq,  maxlen=MAX_LEN)

y_train = np.array(y_train)
y_test  = np.array(y_test)

# Model (same as yours)
model = Sequential([
    Embedding(MAX_WORDS, 64, input_length=MAX_LEN),
    Bidirectional(LSTM(64)),
    Dense(64, activation="relu"),
    Dropout(0.5),
    Dense(3, activation="softmax")
])

model.compile(
    loss="sparse_categorical_crossentropy",
    optimizer="adam",
    metrics=["accuracy"]
)

model.summary()

#Train with early stopping
early_stop = EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True)

history = model.fit(
    X_train_pad, y_train,
    epochs=15,
    batch_size=32,
    validation_split=0.2,
    callbacks=[early_stop],
    verbose=1
)

test_loss, test_acc = model.evaluate(X_test_pad, y_test, verbose=0)
print(f"\nTest accuracy: {test_acc:.4f}")