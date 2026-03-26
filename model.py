import pickle
import re
import string
from typing import Union

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

try:
    import nltk
    from nltk.corpus import stopwords
    nltk.download('stopwords', quiet=True)
    STOPWORDS = set(stopwords.words('english'))
except ImportError:
    STOPWORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
        'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
        'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
        'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
        'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
        'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
        'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
        'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
        'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both',
        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
        'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain',
        'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma',
        'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn'
    }

# Label mapping for interpretable output
LABEL_NAMES = {0: 'Normal', 1: 'Promotional', 2: 'Scam/Spam'}


# ── Text Cleaning ─────────────────────────────────────────────────────────────

def clean_text(
    text: Union[str, list],
    lowercase: bool = True,
    remove_punct: bool = True,
    remove_stops: bool = True,
    remove_nums: bool = False,
    remove_url: bool = True,
    custom_stopwords: set = None
) -> Union[str, list]:
    """Clean text: lowercase, remove URLs/punctuation/stopwords/whitespace."""
    if isinstance(text, list):
        return [clean_text(t, lowercase, remove_punct, remove_stops,
                           remove_nums, remove_url, custom_stopwords) for t in text]

    if not isinstance(text, str):
        raise TypeError(f"Expected str or list, got {type(text).__name__}")

    if remove_url:
        text = re.sub(r'http\S+|www\S+', '', text)
    if lowercase:
        text = text.lower()
    if remove_nums:
        text = re.sub(r'\d+', '', text)
    if remove_punct:
        text = text.translate(str.maketrans('', '', string.punctuation))

    text = re.sub(r'\s+', ' ', text).strip()

    if remove_stops:
        stop_words = STOPWORDS | custom_stopwords if custom_stopwords else STOPWORDS
        text = ' '.join(w for w in text.split() if w not in stop_words)

    return text


# ── Dataset A: Hand-curated Promotional Messages ──────────────────────────────
# Real-world brand/service messages containing words like "free", "offer",
# "win", "discount" that are legitimate marketing — NOT scam.
# Source: manually written based on common Indian & global telecom/e-commerce
# patterns. Expand this list to improve Promotional recall over time.

PROMOTIONAL_CURATED = [
    # Telecom — India (Airtel, Jio, Vi)
    "Dear customer, recharge with Rs.299 and get unlimited calls + 1.5GB/day data for 28 days. Visit airtel.in",
    "Airtel Special Offer: Get 2GB extra data FREE on your next recharge of Rs.199 or above. Valid till Sunday.",
    "Your Airtel postpaid bill of Rs.499 is due on 30th. Pay now and get 10% cashback via Airtel Thanks app.",
    "Exclusive for Airtel users: Upgrade to 5G now and enjoy 3 months of premium streaming at no extra cost.",
    "Hi! As a valued Airtel customer, enjoy Amazon Prime FREE for 3 months on recharge of Rs.599 or above.",
    "Jio Offer: Recharge with Rs.349 and get 2GB/day + unlimited calls for 28 days. Activate now.",
    "Vi Special: Get 3GB/day data for 56 days at Rs.449. Limited period offer for prepaid customers only.",
    # E-commerce — Amazon, Flipkart
    "Amazon Great Indian Sale is LIVE! Up to 70% off on electronics, fashion & more. Shop now: amazon.in",
    "Your Amazon order #402-8821934 has been shipped and will arrive by Thursday. Track your package in the app.",
    "Amazon Prime Day is here! Exclusive deals for Prime members. New deals every 30 mins. Happy shopping!",
    "Reminder: Items in your Amazon cart are selling fast. Complete your purchase before they go out of stock.",
    "Amazon Pay Offer: Get Rs.150 cashback on your next order of Rs.500+. Valid for Prime members only.",
    "Flipkart Big Billion Days Sale starts tomorrow! Up to 80% off on mobiles, TVs and appliances.",
    "Your Flipkart order has been delivered. Rate your experience and earn SuperCoins.",
    "Exclusive Flipkart offer: Buy any smartphone above Rs.10000 and get free earbuds worth Rs.1499.",
    "Flipkart Plus members get early access to sale from 8 PM tonight. Don't miss out!",
    # Food Delivery — Swiggy, Zomato
    "Swiggy: Order now and get 40% off up to Rs.120 on your favourite restaurants. Use code SAVE40.",
    "Zomato Pro: Enjoy unlimited free deliveries and exclusive member discounts on every order.",
    "Your Swiggy order from Domino's is on its way! Estimated delivery: 25 minutes.",
    "Zomato: Flat Rs.75 off on orders above Rs.199 this lunchtime. Order your favourite meal now!",
    # Banking & Payments — HDFC, ICICI, SBI, PhonePe, Paytm
    "Your HDFC Credit Card statement for July is ready. Total due: Rs.4,230. Pay by 15th to avoid charges.",
    "ICICI Bank: Your account was credited with Rs.12,000 on 25-Jul. Check your passbook for details.",
    "PhonePe: You received Rs.500 from Rahul Kumar. Check your PhonePe wallet for details.",
    "Paytm Cashback Alert! You have earned Rs.50 cashback on your last transaction.",
    "SBI: Your FD of Rs.50,000 has matured. Please visit your branch or login to net banking to renew.",
    "HDFC Bank: Congratulations! Your credit card limit has been increased to Rs.2,00,000.",
    # Retail & Fashion — Myntra, Nykaa, Big Bazaar
    "Big Bazaar Weekend Special: Flat 30% off on all grocery items. Offer valid Sat-Sun only at all stores.",
    "Myntra End of Reason Sale: Up to 50-80% off on top brands. Free delivery on all orders above Rs.299.",
    "Nykaa Monsoon Sale: Buy 2 get 1 free on all skincare products.",
    "Reliance Digital Diwali Offer: Exchange your old TV and get up to Rs.10,000 off on new Smart TVs.",
    "Starbucks: Your reward is ready! Redeem 1 free Grande beverage on your next visit. Valid for 7 days.",
    # Services & Apps — BookMyShow, Ola, Uber, Netflix
    "BookMyShow: Reminder - your movie tickets for Jawan (7:30 PM) are confirmed. Enjoy the show!",
    "MakeMyTrip: Flight PNR ABCD12 is confirmed. Check-in opens 48 hours before departure.",
    "Ola: Your ride has been booked. Driver Ramesh is 3 minutes away. OTP: 4521",
    "Uber: Thanks for riding with us! Rate your trip and help your driver maintain their 5-star rating.",
    "Netflix: New season of Sacred Games is now available! Start watching on your Premium plan.",
    "Cult.fit: Your class booking for Yoga (7 AM, Thursday) is confirmed. Don't forget your mat!",
    "PharmEasy: Your medicine order will be delivered by 6 PM today. Stay healthy!",
    "HealthifyMe: You have hit your 10,000 steps goal today! Keep it up and earn your weekly badge.",
    # Generic promotional patterns
    "Dear customer, our annual sale is now live. Visit your nearest store and enjoy exclusive discounts.",
    "Thank you for shopping with us! Use code WELCOME10 for 10% off on your next purchase.",
    "Your subscription has been renewed successfully. Thank you for being a loyal member.",
    "Flash Sale alert: 50% off on selected items for the next 2 hours only. Shop now!",
    "We miss you! Here is a special 20% discount coupon valid for the next 7 days: COMEBACK20",
    "Your reward points are about to expire. Redeem 500 points before 31st August at any of our stores.",
    "New arrivals just dropped! Check out the latest collection on our app. Free shipping on all orders.",
    "Your cashback of Rs.200 has been credited to your wallet. Use it on your next purchase.",
    "Exclusive member offer: Buy 1 get 1 free on all beverages this weekend at participating outlets.",
    "Dear valued customer, your annual plan renews on Aug 1st. Log in to review your plan details.",
]


# ── Dataset B: spam_texts.csv — Labelled subset ───────────────────────────────
# Source: spam_texts.csv (25 real-world marketing SMS messages with images).
# Each row reviewed manually and assigned one of:
#   1 = Promotional (legitimate brand/service marketing)
#   2 = Scam/Spam   (gambling, fraud, unsolicited bulk)
#
# Index → (label, reason)
# [0]  PharmEasy cashback             → 1 Promotional
# [1]  Fashion brand curation link    → 1 Promotional
# [2]  Cleaning services ad           → 1 Promotional (local business)
# [3]  Carrefour app deals            → 1 Promotional
# [4]  MTN Broadband newsletter       → 1 Promotional
# [5]  "Clientele HELP Cover Debi"    → 1 Promotional (insurance, vague but legit)
# [6]  Funny Dynamic Signatures dial  → 1 Promotional (telecom VAS)
# [7]  Telkom 2.5GB data deal         → 1 Promotional
# [8]  Airtel + Smartcash recharge    → 1 Promotional
# [9]  Telenor 50GB discount          → 1 Promotional
# [10] Airtel Digital TV discount     → 1 Promotional
# [11] Careem/GO ride discount        → 1 Promotional
# [12] Study abroad / visa agents     → 2 Scam/Spam (unsolicited education spam)
# [13] J. fashion Ramzan sale         → 1 Promotional
# [14] Safaricom 2GB data deal        → 1 Promotional
# [15] Aviator gambling "WIN!"        → 2 Scam/Spam (gambling scam)
# [16] Railway Furnishers credit      → 1 Promotional (retail credit offer)
# [17] Telecom data + YouTube         → 1 Promotional
# [18] Amazon Drop fashion curation   → 1 Promotional
# [19] CARS24 sell your car           → 1 Promotional
# [20] Edamama brand day baby deals   → 1 Promotional
# [21] Pulse Plan data deal           → 1 Promotional
# [22] Safaricom 1GB special offer    → 1 Promotional
# [23] Dress new arrivals WhatsApp    → 1 Promotional (local retail)
# [24] Timiza savings loan offer      → 1 Promotional (fintech)

SPAM_TEXTS_LABELS = {
    0: 1, 1: 1, 2: 1, 3: 1, 4: 1,
    5: 1, 6: 1, 7: 1, 8: 1, 9: 1,
    10: 1, 11: 1, 12: 2, 13: 1, 14: 1,
    15: 2, 16: 1, 17: 1, 18: 1, 19: 1,
    20: 1, 21: 1, 22: 1, 23: 1, 24: 1,
}


# ── Load & Prepare Data ───────────────────────────────────────────────────────
# Labels: 0 = Normal, 1 = Promotional, 2 = Scam/Spam

# Base dataset (spam.csv): ham → 0 Normal, spam → 2 Scam/Spam
df_base = pd.read_csv("spam.csv", encoding='latin-1')[['Category', 'Message']]
df_base.columns = ['label', 'message']
df_base['label'] = df_base['label'].map({'ham': 0, 'spam': 2})
df_base['source'] = 'spam.csv'

# Dataset A: hand-curated promotional messages
df_curated = pd.DataFrame({
    'label':   1,
    'message': PROMOTIONAL_CURATED,
    'source':  'curated',
})

# Dataset B: spam_texts.csv — load and apply manual labels
df_spam_texts_raw = pd.read_csv("spam_texts.csv")[['text']]
df_spam_texts_raw.columns = ['message']
df_spam_texts_raw['label'] = df_spam_texts_raw.index.map(SPAM_TEXTS_LABELS)
df_spam_texts_raw['source'] = 'spam_texts.csv'

# Combine all three sources, shuffle
df = pd.concat([df_base, df_curated, df_spam_texts_raw], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df['cleaned_message'] = df['message'].apply(clean_text)

print("Dataset composition:")
for code, name in LABEL_NAMES.items():
    subset = df[df['label'] == code]
    by_source = subset['source'].value_counts().to_dict()
    print(f"  {name:13s} ({code}): {len(subset):>5} samples  {by_source}")

# ── Vectorize & Split ─────────────────────────────────────────────────────────

vectorizer = TfidfVectorizer(max_features=3000)
X = vectorizer.fit_transform(df['cleaned_message'])
y = df['label']

# stratify=y ensures all 3 classes appear proportionally in train and test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Train & Evaluate ──────────────────────────────────────────────────────────
# LogisticRegression: natively multi-class, class_weight compensates imbalance
# MultinomialNB: multi-class native, but struggles with minority classes

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, class_weight='balanced'),
    "Naive Bayes":         MultinomialNB(),
}

for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"\n{'=' * 50}")
    print(f"  {name}")
    print(f"{'=' * 50}")
    print(f"  Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"\n  Confusion Matrix (rows=actual, cols=predicted):")
    print(f"  Classes : {list(LABEL_NAMES.values())}")
    print(confusion_matrix(y_test, y_pred))
    print(f"\n  Classification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=list(LABEL_NAMES.values()),
        zero_division=0
    ))

# ── Save Best Model & Vectorizer ──────────────────────────────────────────────
# Logistic Regression saved as production model — handles class imbalance
# better than Naive Bayes via class_weight='balanced'.

for filename, obj in [('spam_classifier.pkl', models['Logistic Regression']),
                      ('tfidf_vectorizer.pkl', vectorizer)]:
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)

print("\n✓ Saved: spam_classifier.pkl, tfidf_vectorizer.pkl")