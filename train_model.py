# train_model.py
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, GlobalAveragePooling1D, Dropout, LSTM, Bidirectional
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.callbacks import EarlyStopping
import numpy as np
import pickle

# Expanded dataset
# 0 = spam/info/no reply, 1 = reply needed, 2 = urgent reply

texts = [
    # --- Spam / Informational (0) ---
    "Uber One membership perks, free delivery, limited promo code",
    "Quicksilver Credit Card balance update: $408.54 as of October 1",
    "Weekly newsletter from company",
    "Promotion: 50% off limited time",
    "Your package has shipped",
    "Your account statement is ready",
    "FYI update on your subscription",
    "LinkedIn notification: someone viewed your profile",
    "Spotify receipt for monthly payment",
    "Amazon purchase confirmation",
    "Your order has been delivered",
    "Monthly bill is ready for review",
    "Netflix subscription payment processed",
    "Automated system notification, no reply required",
    "Promotional email from airline with discounts",
    "Unsubscribe to stop receiving these emails",
    "Discount code valid until tomorrow",
    "Security alert: new login detected",
    "Thank you for your purchase",
    "This is an automated reply, do not respond",
    "Special offer for premium users",
    "Flash sale ending soon, act now",
    "Join our rewards program today",
    "Congratulations, you have won a coupon",
    "Survey invitation, optional participation",
    "Event reminder: webinar at 3pm",
    "Your password reset request was successful",
    "Welcome to our service, setup your profile",
    "Confirm your email address to complete signup",
    "Invitation to networking event",
    "Marketing email about new features",
    "Daily deals curated for you",
    "Low balance alert from your bank",
    "Free trial ending soon notification",
    "New device sign-in detected",
    "Here is your e-ticket for the flight",
    "Update: new version of app released",
    "Spotify family plan invitation",
    "Payment receipt for online course",
    "Google account activity notification",
    "Promotional: double points this weekend",
    "Reminder: subscription auto-renews tomorrow",
    "Service outage notification",
    "Weekly blog digest from subscribed site",
    "Limited time holiday sale",
    "Thanks for signing up for the newsletter",
    "Download your invoice from attached file",
    "Notification: your parcel is arriving today",
    "Welcome to our loyalty program",
    "Your booking confirmation is attached",

    # --- Reply needed (1) ---
    "Can you send me the report?",
    "What time is the meeting?",
    "Please confirm your attendance",
    "Need your input on this project",
    "Could you help me with this issue?",
    "When are you available to discuss?",
    "Please review the attached document",
    "Can we schedule a call?",
    "Do you agree with this proposal?",
    "Need approval for budget request",
    "Can you clarify the details in the document?",
    "Would you be able to join the meeting?",
    "Let me know your feedback on the draft",
    "Could you send me the contact details?",
    "Please approve the attached expense report",
    "Do you have time to review this today?",
    "Can you provide the updated timeline?",
    "Would you confirm receipt of this email?",
    "Could you update me on project status?",
    "Please share your availability for next week",
    "Do you think this approach works?",
    "Kindly check the attached spreadsheet",
    "Would you mind proofreading this?",
    "Please sign the attached form",
    "Do you know the answer to this question?",
    "What’s your opinion on this idea?",
    "Can you give me an estimate?",
    "Do you have bandwidth to help on this?",
    "Please let me know if you are interested",
    "Could you upload the file to the drive?",
    "Do you want to attend this conference?",
    "Please RSVP by Friday",
    "Can you draft a reply to the client?",
    "Let’s set up a meeting to discuss",
    "Please approve or reject the request",
    "Would you mind checking this bug?",
    "Do you have any suggestions?",
    "Could you connect me with the right person?",
    "Please update the shared document",
    "Would you be open to a quick chat?",
    "Can you confirm if you received this?",
    "Do you want to proceed with this option?",
    "Please double-check these calculations",
    "Could you review the proposal by Monday?",
    "Would you like me to finalize the draft?",
    "Do you agree with these changes?",
    "Can you check if the system is up?",
    "Please confirm the shipping details",
    "Would you approve the attached slides?",
    "Do you think this is the right priority?",

    # --- Urgent reply needed (2) ---
    "Urgent meeting tomorrow at 10am",
    "Deadline is today please respond ASAP",
    "Emergency server down need help immediately",
    "Client angry needs immediate response",
    "Critical bug found in production system",
    "Security breach, immediate action required",
    "Payment overdue, reply today",
    "Project meeting moved to now, confirm attendance",
    "Urgent approval needed for contract",
    "Crisis situation, call me now",
    "Immediate response required on project deliverable",
    "ASAP feedback required for client proposal",
    "Server outage affecting customers, urgent fix needed",
    "Respond today to avoid penalty",
    "Need urgent approval for budget extension",
    "Production system failure requires immediate attention",
    "Reply now or project will be delayed",
    "System down, all users affected, urgent support needed",
    "Payment failure, resolve immediately",
    "Escalation: customer complaint needs urgent response",
    "Board requires immediate confirmation of report",
    "Fire drill meeting happening in 10 minutes",
    "Critical error in financial data, check now",
    "CEO requesting urgent update",
    "Deadline missed, urgent action needed",
    "Meeting rescheduled to now, join immediately",
    "Server compromised, urgent action required",
    "Reply within the hour to confirm",
    "Blocking issue, needs urgent review",
    "Contract signature required today",
    "ASAP bug fix before deployment",
    "Respond before end of day or deal falls through",
    "Delivery delayed, urgent confirmation required",
    "Important compliance report overdue, reply needed",
    "Payment authorization needed urgently",
    "Critical client issue must be resolved today",
    "Downtime alert, urgent engineering help required",
    "Investor call scheduled now, urgent join",
    "Emergency maintenance in 5 minutes",
    "Action required immediately for data loss issue",
    "Critical task pending, needs urgent input",
    "Confirm attendance to crisis meeting now",
    "Immediate correction required in report",
    "High priority incident, reply needed",
    "ASAP join Zoom meeting",
    "Deadline in one hour, respond now",
    "Escalated issue: client waiting on urgent reply",
    "Need urgent approval from your side",
    "Emergency request, action required today",
    "Final notice, respond immediately"
]

labels = (
    [0]*50 +  # spam/info
    [1]*50 +  # reply
    [2]*50    # urgent
)

print(f"Training dataset size: {len(texts)}")
print(f"Class balance: spam={labels.count(0)}, reply={labels.count(1)}, urgent={labels.count(2)}")

# Tokenize
MAX_WORDS = 10000
MAX_LEN = 50

tokenizer = Tokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
padded = pad_sequences(sequences, maxlen=MAX_LEN)

# Model
model = Sequential([
    Embedding(MAX_WORDS, 64, input_length=MAX_LEN),
    Bidirectional(LSTM(64)),
    Dense(64, activation='relu'),
    Dropout(0.5),
    Dense(3, activation='softmax')
])

model.compile(
    loss='sparse_categorical_crossentropy',
    optimizer='adam',
    metrics=['accuracy']
)

print("\nModel architecture:")
model.summary()

# Train with early stopping
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

print("\nTraining model...")
history = model.fit(
    padded, np.array(labels),
    epochs=30,
    validation_split=0.2,
    callbacks=[early_stop],
    verbose=1
)

# Save model + tokenizer
model.save("email_classifier.h5")
with open("tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f)

print("\n✅ Model and tokenizer saved: email_classifier.h5, tokenizer.pkl")
