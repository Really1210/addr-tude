import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
from io import BytesIO

# 네이버 API 정보임
CLIENT_ID = 'buzzqnu77m'
CLIENT_SECRET = 'QkOrNDd4v57qIR2WKrE1gNO7WKKYeiXUMtjjfTAN'

# Geocoding API 호출 함수ff
def get_coordinates(address):
    url = f"https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": CLIENT_ID,
        "X-NCP-APIGW-API-KEY": CLIENT_SECRET
    }
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    try:
        data = response.json()
        if data.get('meta', {}).get('totalCount', 0) > 0:
            lat = data['addresses'][0]['y']
            lon = data['addresses'][0]['x']
            return float(lat), float(lon)
        else:
            return None, None
    except Exception as e:
        st.error(f"API 호출 오류: {e}")
        return None, None

# 스트림릿 UI
st.title("주소로 위경도 찾기 ")
st.write("네이버 지도 API를 사용하여 주소를 위경도로 변환합니다.")

# 주소 입력 방식 선택
input_mode = st.radio("주소 입력 방식을 선택하세요", ("CSV 파일 업로드", "직접 입력"))

# 주소 데이터 처리
addresses = []
if input_mode == "CSV 파일 업로드":
    uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if 'address' in df.columns:
                addresses = df['address'].tolist()
            else:
                st.error("CSV 파일에 'address' 열이 없습니다.")
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")
else:
    address_input = st.text_area("주소를 한 줄에 하나씩 입력하세요")
    if address_input:
        addresses = address_input.split("\n")

# 결과 처리
if st.button("위경도 변환"):
    if addresses:
        results = []
        for address in addresses:
            lat, lon = get_coordinates(address)
            results.append({"주소": address, "위도": lat, "경도": lon})
        
        result_df = pd.DataFrame(results)
        
        # 결과 표시
        st.subheader("변환 결과 ")
        st.dataframe(result_df)
        
        # 엑셀 파일 다운로드 링크 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False)
        output.seek(0)  # BytesIO 객체의 시작 부분으로 이동
        st.download_button(
            label="엑셀 파일로 다운로드",
            data=output,
            file_name="coordinates.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # 지도 시각화
        st.subheader("지도 시각화")
        map_data = result_df.dropna(subset=["위도", "경도"])
        if not map_data.empty:
            st.pydeck_chart(
                pdk.Deck(
                    map_style='mapbox://styles/mapbox/streets-v11',
                    initial_view_state=pdk.ViewState(
                        latitude=map_data["위도"].mean(),
                        longitude=map_data["경도"].mean(),
                        zoom=10,
                        pitch=0,
                    ),
                    layers=[
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=map_data,
                            get_position="[경도, 위도]",
                            get_radius=200,
                            get_color=[0, 0, 255],
                            pickable=True,
                        ),
                    ],
                )
            )
        else:
            st.warning("유효한 위경도 데이터가 없습니다.")
    else:
        st.error("주소를 입력하세요.")
