import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import streamlit as st



Delimiter = st.text_input("Delimiter", ",")
st.write('Please uplaod the queried data')
uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"], accept_multiple_files=False)

data = pd.read_csv(uploaded_file, sep=f"{Delimiter}")

# if uploaded_file is not None:
#     # To read file as bytes:
#     # Can be used wherever a "file-like" object is accepted:
#     try:
#         data = pd.read_csv(uploaded_file, sep=f"{Delimiter}")
#     except:
#         data = pd.read_excel(uploaded_file, sep=f"{Delimiter}")


# data = pd.read_csv('/Users/nineleaps/Downloads/081d31b4-b991-4cbf-a76c-1cfce9725594.csv')
interest_rate = data.groupby(['interest_rate']).agg({'interest_rate': 'count', 'npa_tag': 'mean'})

# Rename the columns for clarity
interest_rate = interest_rate.rename(columns={'npa_tag': 'risk', 'interest_rate': 'total_count'})

# Calculate the ratio
interest_rate['risk'] = interest_rate['risk'] * 100
interest_rate = interest_rate.reset_index()

# Group by 'interest_rate' and calculate the sum of 'npa_tag' and the count of rows
data = data.groupby(['interest_rate', 'loan_amount']).agg({'npa_tag': 'mean'})

# Rename the columns for clarity
data = data.rename(columns={'npa_tag': 'risk'})

# Calculate the ratio
data['risk'] = data['risk'] * 100
data = data.reset_index()
# Define independent features (X) and the target variable (y)
X = data[['interest_rate', 'loan_amount']]
y = data['risk']

st.write(
    f"Desired Hurdle rate is equal to {data.risk.mean() * 100 + 7 + 4}% and Net Risk is {data.risk.mean() * 100}%")

st.write("Interest rate vs risk table")
st.write(interest_rate)

# Normalize 'total_count' values to a color range
norm = Normalize(vmin=interest_rate['total_count'].min(), vmax=interest_rate['total_count'].max())

# Use the normalized values for color
colors = plt.cm.viridis(norm(interest_rate['total_count']))

# Create the bar graph with color intensity
plt.bar(interest_rate['interest_rate'], interest_rate['risk'], color=colors, edgecolor='black', alpha=0.7)

# Set labels and title
plt.xlabel('Interest Rate')
plt.ylabel('Risk')
plt.title('Bar Graph with Color Intensity')

# Show the color bar for 'total_count'
color_bar = plt.colorbar(plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=norm))
color_bar.set_label('Total Count')

# Display the plot
# plt.show()
st.write("Plot for interest rate vs Risk")
st.pyplot(plt)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# Create a decision tree regressor with hyperparameters to control overfitting
regressor = DecisionTreeRegressor(max_depth=15, min_samples_split=100, min_samples_leaf=50)
regressor.fit(X_train, y_train)
y_pred = regressor.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
# st.write((f'Mean Squared Error: {mse}'))
# print(f'R-squared: {r2}')

ir = st.text_input("Choose the Interest Rate To Predict The Risk", 16)
lm = st.text_input("Choose the Loan Amount To Predict The Risk", 50000)
yp = regressor.predict(pd.DataFrame({"interest_rate": [f"{ir}"], "loan_amount": [f"{lm}"]}))
st.write(f"Predicted Risk is equal to {yp[0]}%")
