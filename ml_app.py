import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# from palmerpenguins import load_penguins
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score


# 페이지 타이틀 설정
st.set_page_config(page_title="머신 러닝 앱",page_icon='🤖', layout="wide")

st.title('💻 머신 러닝 앱')

# info(): 파란색 배경의 글 작성
st.info('머신러닝 모델을 구축하는 앱 입니다!')

# @st.cache_data
def load_data():
    return pd.read_csv("https://raw.githubusercontent.com/gnu-mot/visualization/refs/heads/main/lecture12.csv")
    #return pd.read_csv("/content/lecture12.csv")

# 데이터 불러오기
df = load_data()


# Expander (확장자) 사용
with st.expander('Data'):
  st.write('**Raw data(원본 데이터)**')
  df.head()

  st.write('**X**')
  X_raw = df.drop('species', axis=1)
  st.dataframe(X_raw)

  st.write('**y**')
  y_raw = df['species']
  y_raw # st.dataframe 불필요 (st.dataframe 없이 표현 가능)

with st.expander('Data visualization'):
  options = st.multiselect(
      "시각화를 희망하는 변수를 선택하세요",
      ["bill_length_mm", "bill_depth_mm","flipper_length_mm",	"body_mass_g"],
      ["bill_length_mm", "bill_depth_mm"] )
  if len(options) >= 2:
        st.scatter_chart(
            data=df,
            x=options[0],
            y=options[1],
            color='species'
        )
  else:
        st.warning("적어도 두 개의 변수를 선택하세요.")

# 머신러닝 모델의 선택
classifier_name = st.sidebar.selectbox(
    '원하는 모델을 선택하세요.',
    ('KNN', 'SVM', 'Random Forest')
)

# 머신러닝 모델의 하이퍼파라미터 조정
def add_parameter_ui(clf_name):
    params = dict()
    if clf_name == 'SVM': # default 1.0
        C = st.sidebar.slider('C', 0.01, 10.0, 1.0)
        params['C'] = C
        gamma = st.sidebar.selectbox("감마 값의 선택",("auto", "scale"))
    elif clf_name == 'KNN':
        neighbors = st.sidebar.slider('K', 1, 15, 5)
        params['n_neighbors'] = neighbors
    else: # Random Forest를 지칭
        max_depth = st.sidebar.slider('max_depth', 2, 15, None)
        params['max_depth'] = max_depth
        n_estimators = st.sidebar.slider('n_estimators', 100, 500, 100)
        params['n_estimators'] = n_estimators
    return params

params = add_parameter_ui(classifier_name)

#  분류기의 선택
def get_classifier(clf_name, params):
    clf = None
    if clf_name == 'SVM':
        clf = SVC(C=params['C'], random_state=2024, probability=True)
    elif clf_name == 'KNN':
        clf = KNeighborsClassifier(n_neighbors=params['n_neighbors'])
    else:
        clf = RandomForestClassifier(n_estimators=params['n_estimators'],
            max_depth=params['max_depth'], random_state=2024)
    return clf


def encode_categorical(df):
    le = LabelEncoder()
    for column in ['island', 'sex']:
        if column in df.columns:
            df[column] = le.fit_transform(df[column].astype(str))
    return df

# 입력 변수 (사이드바 부분)
with st.sidebar:
  st.header('입력변수 창')
  island = st.selectbox('Island', ('Biscoe', 'Dream', 'Torgersen'))
  bill_length_mm = st.slider('Bill length (mm)', 32.1, 59.6, 43.9)
  bill_depth_mm = st.slider('Bill depth (mm)', 13.1, 21.5, 17.2)
  flipper_length_mm = st.slider('Flipper length (mm)', 172.0, 231.0, 201.0)
  body_mass_g = st.slider('Body mass (g)', 2700.0, 6300.0, 4207.0)
  gender = st.selectbox('Gender', ('male', 'female'))

  # 입려된 값으로 데이터 프레임 생성
  data = {'island': island,
          'bill_length_mm': bill_length_mm,
          'bill_depth_mm': bill_depth_mm,
          'flipper_length_mm': flipper_length_mm,
          'body_mass_g': body_mass_g,
          'sex': gender}
  input_df = pd.DataFrame(data, index=[0])
  input_df = encode_categorical(input_df)
  X_raw = encode_categorical(X_raw)
  input_penguins = pd.concat([input_df, X_raw], axis=0)


with st.expander('입력 데이터'):
  st.write('**예측하고자 하는 값**')
  input_df
  st.write('**전체 데이터**')
  input_penguins


# 데이터 변환
# X 변수 처리

X = input_penguins[1:]
input_row = input_penguins[:1]

# y 변수 처리
target_mapper = {'Adelie': 0,
                 'Chinstrap': 1,
                 'Gentoo': 2}

def target_encode(val):
  return target_mapper[val]

y_encoded = y_raw.apply(target_encode)

# 학습과 검증으로 구분
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=2024)

X_train.head()

with st.expander('활용 데이터'):
  st.write('**Encoded X (input penguin)**')
  input_row


# 모델 학습 및 예측
## 모델의 학습
clf = get_classifier(classifier_name, params)

clf.fit(X_train, y_train)

## 학습 모델을 활용한 예측값 도출
y_pred = clf.predict(X_test)
# st.write(prediction)
acc = accuracy_score(y_test, y_pred)
st.write(f'Classifier = {classifier_name}')
st.write(f'Accuracy =', acc)


# PCA로 축약해서 표현
pca = PCA(2)
X_projected = pca.fit_transform(X_raw)

x1 = X_projected[:, 0]
x2 = X_projected[:, 1]

fig = plt.figure()
plt.scatter(x1, x2, c=y_encoded,
        alpha=0.8,
        cmap='viridis')

plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.colorbar()

st.pyplot(fig)


## 단순 분류를 넘어, 확률을 도출

prediction_proba = clf.predict_proba(input_row)
prediction = clf.predict(input_row)

df_prediction_proba = pd.DataFrame(prediction_proba)
df_prediction_proba.columns = ['Adelie', 'Chinstrap', 'Gentoo']
df_prediction_proba.rename(columns={0: 'Adelie',
                                 1: 'Chinstrap',
                                 2: 'Gentoo'})

# 결과값 시각화
st.subheader('Predicted Species')
st.dataframe(df_prediction_proba,
             column_config={
               'Adelie': st.column_config.ProgressColumn(
                 'Adelie',
                 format='%.4f',
                 width='medium',
                 min_value=0,
                 max_value=1
               ),
               'Chinstrap': st.column_config.ProgressColumn(
                 'Chinstrap',
                 format='%.4f',
                 width='medium',
                 min_value=0,
                 max_value=1
               ),
               'Gentoo': st.column_config.ProgressColumn(
                 'Gentoo',
                 format='%.4f',
                 width='medium',
                 min_value=0,
                 max_value=1
               ),
             }, hide_index=True)




penguins_species = np.array(['Adelie', 'Chinstrap', 'Gentoo'])
st.success(f"Predicted species: {penguins_species[prediction[0]]}")
