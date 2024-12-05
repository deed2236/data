import pandas as pd
pd.set_option('display.max_columns', None)
import pycountry
import streamlit as st
import time
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 페이지 설정 (스크립트의 최상단에 위치해야 함)
st.set_page_config(page_title='데이터 시각화 - 앱', page_icon='📑', layout="wide")

# 데이터 캐싱: 데이터를 한 번만 로드
@st.cache_data
def load_data():
    data = pd.read_csv('https://raw.githubusercontent.com/deed2236/data/main/purchase.csv')

    # 국가 코드 (ISO Alpha-2)와 국가명 매핑 함수
    def get_country_name(country_code):
        try:
            return pycountry.countries.get(alpha_2=country_code).name
        except:
            return None  # 매핑되지 않는 경우 NaN 처리

    # ISO Alpha-2 코드를 ISO Alpha-3 형식으로 변환하는 함수
    def convert_to_iso3(code):
        try:
            return pycountry.countries.get(alpha_2=code).alpha_3
        except:
            return None

    #데이터에서 year 칼럼 생성 ( delivery_date 기준으로 )
    data['year'] = pd.to_datetime(data['delivery_date']).dt.year

    # 국가 이름 열 추가
    data['country_name'] = data['country'].apply(get_country_name)

    # ISO Alpha-3 코드 열 추가
    data['country'] = data['country'].apply(convert_to_iso3)

    # 'year' 열을 문자열로 변환
    data['year'] = data['year'].astype(str)

    return data

# 데이터 로딩
main_data = load_data()

# 트리 메뉴 생성
with st.sidebar:
    menu_selection = option_menu(
        "메뉴",               # 메뉴 제목
        # ["메인 데이터", "데이터 그래프", "설정"],  # 메뉴 항목
        # icons=["house", "bar-chart", "gear"],  # 아이콘 (Bootstrap Icons 사용)
        ["메인 데이터", "국가별 발주그래프", "연도별 발주그래프", "공급업체별 발주그래프", "물종별 발주그래프"],  # 메뉴 항목
        icons=["house", "bar-chart", "bar-chart", "bar-chart", "bar-chart"],  # 아이콘 (Bootstrap Icons 사용)
        menu_icon="cast",         # 메인 메뉴 아이콘
        default_index=0,          # 기본 선택 항목
        orientation="vertical",   # 세로 방향
    )

# 각 메뉴에 따른 화면 렌더링
if menu_selection == "메인 데이터":
    st.title("메인 데이터 목록")
    st.write("기본 데이터 확인하는 화면입니다.")

    # AgGrid 옵션 빌더 설정
    gb = GridOptionsBuilder.from_dataframe(main_data)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100)  # 페이지 크기 설정
    gb.configure_default_column(resizable=True, sortable=True, filterable=True)  # 기본 열 설정
    #gb.configure_selection('multiple', use_checkbox=True)  # 다중 선택 기능 활성화
    gb.configure_grid_options(enableCopyToClipboard=True)  # 복사 기능 활성화
    gb.configure_grid_options(enableExportToExcel=True)  # 엑셀 다운로드 기능 활성화

    grid_options = gb.build()

    # AgGrid에 데이터 표시
    AgGrid(
        main_data,
        gridOptions=grid_options,
        height=1000,
        theme="streamlit",
        enable_enterprise_modules=False,
    )

elif menu_selection == "국가별 발주그래프":
    st.title("연도기준 국가별 발주그래프")
    st.write("세계지도 기준")
    # 연도 리스트 생성
    years = sorted(main_data['year'].unique())

    # Streamlit에서 연도 선택 필터 만들기
    selected_year = st.selectbox("연도 선택", years, index=0)

    year_country_df = main_data.groupby(['country', 'country_name', 'year'])['total_price_krw'].sum().reset_index()

    # 연도별 데이터 필터링
    year_country_df = year_country_df[year_country_df['year'] == selected_year]

    # 대화형 choropleth 맵 생성
    fig = go.Figure()

    # 국가별 발주 금액 데이터를 사용하여 Choropleth 맵 그리기
    fig.add_trace(go.Choropleth(
        locations=year_country_df['country'],  # 국가 코드 (ISO Alpha-3 형식)
        locationmode='ISO-3',                  # ISO-3 형식 사용
        z=year_country_df['total_price_krw'],  # 색상으로 표시할 데이터 (총 구매 금액)
        hoverinfo='text',                      # 마우스 호버 시 표시할 정보
        text=year_country_df.apply(
            lambda row: f"{row['country_name']}({row['country']}): {row['total_price_krw']:,} ", axis=1),
        showscale=True,                        # 색상 스케일 표시
        colorscale='Viridis',                  # 색상 스케일 설정
        colorbar=dict(                         # 색상 바 설정
            titleside='right'
        )
    ))

    # 맵 설정
    fig.update_layout(
        #title=f"{selected_year}년",  # 제목을 선택된 연도로 설정
        #title_x=0.5,  # 제목을 가운데 정렬
        font=dict(
            size=24  # 제목의 폰트 크기 설정
        ),
        geo=dict(
          showframe=True,            # 전체 지도 프레임 표시
          #showcoastlines=True,       # 해안선 표시
          coastlinecolor="Black",    # 해안선 색상
          projection_type="natural earth",  # 자연 지구형 지도 설정
          landcolor="white",         # 육지 색상 설정
          subunitcolor="grey",       # 국가 경계 색상
        ),
        #width=1200,  # 전체 그림의 너비 증가
        height=700,  # 전체 그림의 높이 증가
    )

    # 결과 출력
    st.plotly_chart(fig)

    st.write("국가별 발주데이터")
    # Streamlit에서 전체 화면 너비로 테이블 표시
    st.dataframe(year_country_df, use_container_width=True)

elif menu_selection == "연도별 발주그래프":
    st.title("연도별 발주그래프")
    st.write("연도별 발주그래프")

    # 연도별 총 구매 금액 계산
    year_data = main_data.groupby('year').agg(
      total_price_krw=('total_price_krw', 'sum')
    ).reset_index()

    fig = go.Figure()

    # 라인 그래프 표현
    fig.add_trace(go.Scatter(x=year_data['year'], y=year_data['total_price_krw'], name='총 구매', mode='lines+markers', line=dict(color='royalblue', width=2), hovertemplate=('연도: %{x}<br>구매 금액: %{y:,} KRW<extra></extra>')))

    # 레이아웃 설정
    fig.update_layout(
        xaxis_title='연도',
        yaxis_title='발주 금액 (KRW)',
        xaxis=dict(
          tickmode='linear',
          dtick=1  # 1년 단위로 눈금 표시
        )
    )

    st.plotly_chart(fig)

    st.write("연도별 발주데이터")
    # Streamlit에서 전체 화면 너비로 테이블 표시
    st.dataframe(year_data, use_container_width=True)

    st.write("연도별 발주그래프(내자/외자)")
    # 'country'가 'kor'인 데이터만 필터링하고, 연도별 'total_price_krw' 합계 계산 ( 내자 )
    kor_data = main_data[main_data['country'] == 'KOR'].groupby('year')['total_price_krw'].sum().reset_index()

    # 'country'가 'kor'이 아닌 데이터만 필터링하고, 연도별 'total_price_krw' 합계 계산 ( 외자 )
    not_kor_data = main_data[main_data['country'] != 'KOR'].groupby('year')['total_price_krw'].sum().reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=kor_data['year'], y=kor_data['total_price_krw'], name='내자', mode='lines+markers', line=dict(color='royalblue', width=2), hovertemplate=('연도: %{x}<br>구매 금액: %{y:,} KRW<extra></extra>')))
    fig.add_trace(go.Scatter(x=not_kor_data['year'], y=not_kor_data['total_price_krw'], name='외자', mode='lines+markers', line=dict(color='firebrick', width=2), hovertemplate=('연도: %{x}<br>구매 금액: %{y:,} KRW<extra></extra>')))

    # 레이아웃 설정
    fig.update_layout(
        xaxis_title='연도',
        yaxis_title='발주 금액 (KRW)',
        xaxis=dict(
            tickmode='linear',
            dtick=1  # 1년 단위로 눈금 표시
        ),
        font=dict(
            size=14
        ),
        legend=dict(
            title='구분',
            x=0.92,  # 그래프 안쪽의 오른쪽에 위치
            y=0.92,  # 그래프 상단에 위치
          # traceorder='normal',
            bgcolor='rgba(255, 255, 255, 0.5)',  # 투명도를 가진 배경색
            bordercolor='gray',
            borderwidth=1
        )
    )
    st.plotly_chart(fig)

    # 컬럼을 2개로 나누기
    col1, col2 = st.columns(2)

    # 첫 번째 컬럼: 연도별 발주데이터(계획)
    with col1:
        st.write("연도별 발주데이터(내자)")
        st.dataframe(kor_data, use_container_width=True)

    # 두 번째 컬럼: 연도별 발주데이터(실적)
    with col2:
        st.write("연도별 발주데이터(외자)")
        st.dataframe(not_kor_data, use_container_width=True)

    st.write("연도별 발주그래프(계획/실적)")

    # 연도별 총 구매 금액 계산
    plan_year_data = main_data.groupby('year').agg(
      receive_total_price_krw=('receive_total_price_krw', 'sum')
    ).reset_index()

    fig = go.Figure()

    fig.add_trace(go.Bar(x=year_data['year'], y=year_data['total_price_krw'], name='계획', marker_color='red', hovertemplate=('연도: %{x}<br>구매 금액: %{y:,} KRW<extra></extra>')))
    fig.add_trace(go.Bar(x=plan_year_data['year'], y=plan_year_data['receive_total_price_krw'], name='실적', marker_color='blue', hovertemplate=('연도: %{x}<br>구매 금액: %{y:,} KRW<extra></extra>')))

    # 레이아웃 설정
    fig.update_layout(
        xaxis_title='연도',
        yaxis_title='금액 (KRW)',
        xaxis=dict(
            tickmode='linear',
            dtick=1  # 1년 단위로 눈금 표시
        ),
        font=dict(
            size=14
        ),
        legend=dict(
            title='구분',
            x=0.92,  # 그래프 안쪽의 오른쪽에 위치
            y=0.92,  # 그래프 상단에 위치
          # traceorder='normal',
            bgcolor='rgba(255, 255, 255, 0.5)',  # 투명도를 가진 배경색
            bordercolor='gray',
            borderwidth=1
        )
    )
    st.plotly_chart(fig)

    # 컬럼을 2개로 나누기
    col1, col2 = st.columns(2)

    # 첫 번째 컬럼: 연도별 발주데이터(계획)
    with col1:
        st.write("연도별 발주데이터(계획)")
        st.dataframe(year_data, use_container_width=True)

    # 두 번째 컬럼: 연도별 발주데이터(실적)
    with col2:
        st.write("연도별 발주데이터(실적)")
        st.dataframe(plan_year_data, use_container_width=True)

elif menu_selection == "공급업체별 발주그래프":
    st.title("공급업체별 발주그래프")
    st.write("공급업체별 발주그래프")

    # 연도 리스트 생성
    years = sorted(main_data['year'].unique())

    # Streamlit에서 연도 선택 필터 만들기
    selected_year = st.selectbox("연도 선택", years, index=0)

    # 공급업체별 기준
    # total_price_krw와 receive_total_price_krw의 합계 계산
    supplier_df = main_data.groupby(['supplier', 'supplier_name', 'year']).agg(
      total_price_krw=('total_price_krw', 'sum')
    ).reset_index()

    # 연도별 데이터 필터링
    pie_supplier_df = supplier_df[supplier_df['year'] == selected_year]

    # 대화형 choropleth 맵 생성
    fig = go.Figure()

    # 국가별 발주 금액 데이터를 사용하여 Choropleth 맵 그리기
    fig.add_trace(go.Pie(
                labels=pie_supplier_df['supplier_name'],
                values=pie_supplier_df['total_price_krw'],
                name=str(selected_year),  # 연도 이름을 파이 그래프 이름으로 설정
                hole=0.4,  # 도넛 형태
                textinfo='none',  # 레이블과 비율 표시
                text=pie_supplier_df.apply(
                    lambda row: f"{row['supplier_name']} [ {row['supplier']} ] - {row['total_price_krw']:,} ", axis=1),
                hoverinfo='text'  # 마우스 호버 시 레이블과 값 표시
            )
    )

    # 그래프 설정
    fig.update_layout(
        font=dict(size=24),  # 제목 폰트 크기 설정
    #    width=800,  # 전체 그림의 너비
    #    height=2000,  # 전체 그림의 높이
    )

    # 결과 출력
    st.plotly_chart(fig)

    st.write("공급업체별 발주데이터")
    st.dataframe(pie_supplier_df, use_container_width=True)

    st.write("연도별 발주그래프 - 공급업체기준")
    # supplier_name과 supplier 기준으로 고유값 추출
    suppliers = supplier_df[['supplier', 'supplier_name']].drop_duplicates()

    fig = go.Figure()

    #iterrows()로 각 행을 순회
    for index, supplier in suppliers.iterrows():
      inner_df = supplier_df[supplier_df['supplier'] == supplier['supplier']]

      fig.add_trace(
        go.Scatter(
              x=inner_df['year']
              , y=inner_df['total_price_krw']
              , name=supplier['supplier_name']
              , mode='lines+markers'
              , line=dict(width=2)
              , hovertemplate=('업체: %{text}<br>연도: %{x}<br>구매 금액: %{y:,} KRW<extra></extra>')
              , text=[supplier['supplier_name']] * len(inner_df)  # 모든 데이터 포인트에 대해 text를 반복
            )
        )

    # 레이아웃 설정
    fig.update_layout(
        xaxis_title='연도',
        yaxis_title='금액 (KRW)',
        #height=1000,
        xaxis=dict(
            tickmode='linear',
            dtick=1  # 1년 단위로 눈금 표시
        ),
        font=dict(
            size=14
        ),
        legend=dict(
            x=1,  # 그래프 안쪽의 오른쪽에 위치
            y=1,  # 그래프 상단에 위치
          # traceorder='normal',
            bgcolor='rgba(255, 255, 255, 0.5)',  # 투명도를 가진 배경색
            bordercolor='gray',
            borderwidth=1
        )
    )

    # 결과 출력
    st.plotly_chart(fig)


elif menu_selection == "물종별 발주그래프":
    st.title("물종별 발주그래프")
    st.write("물종별 발주그래프")

    # 연도 리스트 생성
    years = sorted(main_data['year'].unique())

    # Streamlit에서 연도 선택 필터 만들기
    selected_year = st.selectbox("연도 선택", years, index=0)

    # 물종별 기준
    # total_price_krw와 receive_total_price_krw의 합계 계산
    type_df = main_data.groupby(['material_type', 'material_type_name', 'year']).agg(
      total_price_krw=('total_price_krw', 'sum')
    ).reset_index()

    # 연도별 데이터 필터링
    pie_type_df = type_df[type_df['year'] == selected_year]

    # 대화형 choropleth 맵 생성
    fig = go.Figure()

    # 국가별 발주 금액 데이터를 사용하여 Choropleth 맵 그리기
    fig.add_trace(go.Pie(
                labels=pie_type_df['material_type_name'],
                values=pie_type_df['total_price_krw'],
                name=str(selected_year),  # 연도 이름을 파이 그래프 이름으로 설정
                hole=0.4,  # 도넛 형태
                textinfo='none',  # 레이블과 비율 표시
                text=pie_type_df.apply(
                    lambda row: f"{row['material_type_name']} [ {row['material_type']} ] - {row['total_price_krw']:,} ", axis=1),
                hoverinfo='text'  # 마우스 호버 시 레이블과 값 표시
            )
    )

    # 그래프 설정
    fig.update_layout(
        font=dict(size=24),  # 제목 폰트 크기 설정
    #    width=800,  # 전체 그림의 너비
    #    height=2000,  # 전체 그림의 높이
    )

    # 결과 출력
    st.plotly_chart(fig)

    st.write("물종별 발주데이터")
    st.dataframe(pie_type_df, use_container_width=True)

    st.write("연도별 발주그래프 - 공급업체기준")
    # supplier_name과 supplier 기준으로 고유값 추출
    types = type_df[['material_type', 'material_type_name']].drop_duplicates()

    fig = go.Figure()

    #iterrows()로 각 행을 순회
    for index, temp in types.iterrows():
      inner_df = type_df[type_df['material_type'] == temp['material_type']]

      fig.add_trace(
        go.Scatter(
              x=inner_df['year']
              , y=inner_df['total_price_krw']
              , name=temp['material_type_name']
              , mode='lines+markers'
              , line=dict(width=2)
              , hovertemplate=('업체: %{text}<br>연도: %{x}<br>구매 금액: %{y:,} KRW<extra></extra>')
              , text=[temp['material_type_name']] * len(inner_df)  # 모든 데이터 포인트에 대해 text를 반복
            )
        )

    # 레이아웃 설정
    fig.update_layout(
        xaxis_title='연도',
        yaxis_title='금액 (KRW)',
        #height=1000,
        xaxis=dict(
            tickmode='linear',
            dtick=1  # 1년 단위로 눈금 표시
        ),
        font=dict(
            size=14
        ),
        legend=dict(
            x=1,  # 그래프 안쪽의 오른쪽에 위치
            y=1,  # 그래프 상단에 위치
          # traceorder='normal',
            bgcolor='rgba(255, 255, 255, 0.5)',  # 투명도를 가진 배경색
            bordercolor='gray',
            borderwidth=1
        )
    )

    # 결과 출력
    st.plotly_chart(fig)


