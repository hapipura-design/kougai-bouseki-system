import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import io

# ページ設定
st.set_page_config(
    page_title="公害防止管理者 申請書作成システム",
    page_icon="🏭",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
)

# システムクラス
class GLX_Form3_System:
    def __init__(self):
        if 'applicant_data' not in st.session_state:
            st.session_state.applicant_data = {
                "applicant_name": "",
                "target_exam": "",
                "target_exam_code": "",
                "education": "",
                "education_code": "",
                "required_years": 0,
                "experiences": [],
                "certifier": {}
            }
        
        self.exam_types = {
            "1": "大気関係第1種", "2": "大気関係第2種", "3": "大気関係第3種", "4": "大気関係第4種",
            "5": "水質関係第1種", "6": "水質関係第2種", "7": "水質関係第3種", "8": "水質関係第4種",
            "9": "騒音・振動関係", "10": "特定粉じん関係", "11": "一般粉じん関係", "12": "ダイオキシン類関係",
            "13": "公害防止主任管理者"
        }
        
        self.valid_facilities = {
            "大気": ["ボイラー", "加熱炉", "溶解炉", "廃棄物焼却炉", "ガスタービン"],
            "水質": ["パルプ製造施設", "無機顔料製造施設", "自動式車両洗浄施設", "厨房施設"],
            "騒音": ["金属加工機械", "空気圧縮機", "送風機", "織機", "破砕機"],
            "粉じん": ["堆積場", "コンベア", "破砕機", "摩砕機"],
            "ダイオキシン": ["焼却炉(指定規模以上)", "製鋼用電気炉"]
        }
        
        self.education_types = {
            "A": "大学（理系：工・薬・理・農等）",
            "B": "短大・高専（理系）",
            "C": "高校・その他文系大学など",
            "D": "その他（学歴不問）"
        }
    
    def determine_requirements(self, exam_code, edu_code):
        exam_name = self.exam_types.get(exam_code)
        if not exam_name:
            return False, 0, "❌ 無効な講習区分です。"
        
        if "第1種" in exam_name:
            return False, 0, f"⛔ 【審査エラー】{exam_name}は、学歴・実務経験のみでの受講申込はできません。"
        
        edu_name = self.education_types.get(edu_code)
        if not edu_name:
            return False, 0, "❌ 無効な学歴区分です。"
        
        is_type3 = "第3種" in exam_name
        is_chief = "主任管理者" in exam_name
        
        if is_chief:
            years_map = {"A": 5, "B": 7, "C": 9, "D": 12}
            note = "※注意：大気と水質、それぞれの経験が必要です。"
        elif is_type3:
            years_map = {"A": 5, "B": 7, "C": 9, "D": 12}
            note = ""
        else:
            years_map = {"A": 3, "B": 5, "C": 7, "D": 10}
            note = ""
        
        years = years_map[edu_code]
        
        st.session_state.applicant_data["target_exam"] = exam_name
        st.session_state.applicant_data["target_exam_code"] = exam_code
        st.session_state.applicant_data["education"] = edu_name
        st.session_state.applicant_data["education_code"] = edu_code
        st.session_state.applicant_data["required_years"] = years
        
        message = f"✅ あなたの必要実務経験年数は【{years}年以上】です。\n{note}"
        return True, years, message
    
    def add_experience(self, facility, start_date_str, end_date_str, has_report=True):
        if not has_report:
            return False, 0, "⛔ 届出のない施設は実務経験として認められません。"
        
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
            
            if end_date_str.lower() in ['now', '現在', '継続中', '']:
                end_date = datetime.datetime.now()
                end_date_str = "現在継続中"
            else:
                end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
            
            if start_date > datetime.datetime.now():
                return False, 0, "❌ 開始日が未来の日付です。"
            if end_date > datetime.datetime.now():
                return False, 0, "❌ 終了日が未来の日付です。"
            if start_date >= end_date:
                return False, 0, "❌ 終了日は開始日より後である必要があります。"
            
            diff = relativedelta(end_date, start_date)
            months = diff.years * 12 + diff.months
            
            if months <= 0:
                return False, 0, "❌ 期間が1ヶ月未満です。"
            
            category = self._get_category(st.session_state.applicant_data["target_exam"])
            
            experience_data = {
                "facility": facility,
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date_str if end_date_str == "現在継続中" else end_date.strftime("%Y-%m-%d"),
                "months": months,
                "category": category
            }
            
            st.session_state.applicant_data["experiences"].append(experience_data)
            
            message = f"✅ {months}ヶ月分を追加しました。（{diff.years}年{diff.months}ヶ月）"
            return True, months, message
        
        except ValueError:
            return False, 0, "❌ 日付形式が正しくありません。"
    
    def _get_category(self, exam_name):
        if "大気" in exam_name or "粉じん" in exam_name:
            return "大気"
        if "水質" in exam_name:
            return "水質"
        if "騒音" in exam_name:
            return "騒音"
        if "ダイオキシン" in exam_name:
            return "ダイオキシン"
        return "その他"
    
    def get_total_months(self):
        return sum(e['months'] for e in st.session_state.applicant_data['experiences'])
    
    def get_total_years_months(self):
        total_months = self.get_total_months()
        return total_months // 12, total_months % 12
    
    def is_requirement_met(self):
        required_months = st.session_state.applicant_data["required_years"] * 12
        return self.get_total_months() >= required_months
    
    def generate_pdf(self, applicant_name, cert_company, cert_name, cert_position):
        try:
            st.session_state.applicant_data["applicant_name"] = applicant_name
            st.session_state.applicant_data["certifier"] = {
                "company": cert_company,
                "name": cert_name,
                "position": cert_position,
                "date": datetime.datetime.now().strftime("%Y年%m月%d日")
            }
            
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            c.setFont('Helvetica-Bold', 16)
            c.drawCentredString(width/2, height - 40*mm, "様式第3")
            c.setFont('Helvetica-Bold', 14)
            c.drawCentredString(width/2, height - 50*mm, "公害防止実務証明書")
            
            y = height - 70*mm
            c.setFont('Helvetica', 10)
            c.drawString(30*mm, y, f"講習区分: {st.session_state.applicant_data['target_exam']}")
            y -= 7*mm
            c.drawString(30*mm, y, f"申請者氏名: {applicant_name}")
            y -= 7*mm
            c.drawString(30*mm, y, f"最終学歴: {st.session_state.applicant_data['education']}")
            y -= 7*mm
            c.drawString(30*mm, y, f"必要実務年数: {st.session_state.applicant_data['required_years']}年以上")
            y -= 7*mm
            total_y, total_m = self.get_total_years_months()
            c.drawString(30*mm, y, f"実務経験合計: {total_y}年{total_m}ヶ月")
            
            y -= 15*mm
            c.setFont('Helvetica-Bold', 11)
            c.drawString(30*mm, y, "【表1】実務経験の内容")
            y -= 7*mm
            
            table_data = [["No.", "施設名", "開始日", "終了日", "期間"]]
            for i, exp in enumerate(st.session_state.applicant_data['experiences'], 1):
                table_data.append([str(i), exp['facility'], exp['start'], exp['end'], f"{exp['months']}ヶ月"])
            
            table = Table(table_data, colWidths=[15*mm, 50*mm, 30*mm, 30*mm, 25*mm])
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            table.wrapOn(c, width, height)
            table.drawOn(c, 30*mm, y - len(table_data) * 7*mm)
            
            y = y - len(table_data) * 7*mm - 20*mm
            c.setFont('Helvetica-Bold', 11)
            c.drawString(30*mm, y, "【証明者情報】")
            y -= 7*mm
            c.setFont('Helvetica', 10)
            c.drawString(30*mm, y, f"事業所名: {cert_company}")
            y -= 7*mm
            c.drawString(30*mm, y, f"役職: {cert_position}")
            y -= 7*mm
            c.drawString(30*mm, y, f"氏名: {cert_name}")
            y -= 10*mm
            c.drawString(30*mm, y, "印: ㊞（※要押印）")
            
            c.setFont('Helvetica', 8)
            c.drawCentredString(width/2, 20*mm, "※この証明書は必ず証明者の印鑑（社印等）を押印の上、提出してください。")
            
            c.save()
            buffer.seek(0)
            return True, buffer
        
        except Exception as e:
            return False, str(e)

# メインアプリ
def main():
    st.title("🏭 公害防止管理者講習 申請書作成システム")
    st.markdown("---")
    
    app = GLX_Form3_System()
    
    # STEP 1: 受講区分と学歴
    st.header("📝 STEP 1: 受講区分と学歴の選択")
    
    col1, col2 = st.columns(2)
    
    with col1:
        exam_choice = st.selectbox(
            "講習区分を選択",
            options=list(app.exam_types.keys()),
            format_func=lambda x: app.exam_types[x]
        )
    
    with col2:
        edu_choice = st.selectbox(
            "最終学歴を選択",
            options=list(app.education_types.keys()),
            format_func=lambda x: app.education_types[x]
        )
    
    if st.button("必要年数を判定", type="primary"):
        success, years, message = app.determine_requirements(exam_choice, edu_choice)
        if success:
            st.success(message)
        else:
            st.error(message)
    
    st.markdown("---")
    
    # STEP 2: 実務経験
    if st.session_state.applicant_data.get("target_exam"):
        st.header("🏢 STEP 2: 実務経験の入力")
        
        total_y, total_m = app.get_total_years_months()
        required_y = st.session_state.applicant_data.get("required_years", 0)
        
        if app.is_requirement_met():
            st.success(f"✅ 現在: {total_y}年{total_m}ヶ月 / 必要: {required_y}年以上 - 必要年数を満たしています！")
        else:
            shortage_months = required_y * 12 - app.get_total_months()
            shortage_y, shortage_m = shortage_months // 12, shortage_months % 12
            st.warning(f"⏳ 現在: {total_y}年{total_m}ヶ月 / 必要: {required_y}年以上 - あと{shortage_y}年{shortage_m}ヶ月必要です")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            facility = st.text_input("施設名", placeholder="例: ボイラー")
        
        with col2:
            start_date = st.date_input("開始日", value=None)
        
        with col3:
            end_date = st.date_input("終了日（継続中の場合は今日）", value=datetime.date.today())
        
        has_report = st.checkbox("行政への設置届出済み", value=True)
        
        if st.button("実務経験を追加"):
            if facility and start_date and end_date:
                success, months, message = app.add_experience(
                    facility,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    has_report
                )
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("すべての項目を入力してください。")
        
        # 登録済み実務経験
        if st.session_state.applicant_data['experiences']:
            st.subheader("📋 登録済み実務経験")
            for i, exp in enumerate(st.session_state.applicant_data['experiences'], 1):
                exp_y, exp_m = exp['months'] // 12, exp['months'] % 12
                st.text(f"{i}. {exp['facility']}: {exp['start']} 〜 {exp['end']} ({exp_y}年{exp_m}ヶ月)")
        
        st.markdown("---")
        
        # STEP 3: PDF生成
        if app.is_requirement_met():
            st.header("📄 STEP 3: PDF生成")
            
            col1, col2 = st.columns(2)
            
            with col1:
                applicant_name = st.text_input("申請者氏名", placeholder="例: 山田太郎")
                cert_company = st.text_input("事業所名", placeholder="例: ○○株式会社 ××工場")
            
            with col2:
                cert_position = st.text_input("証明者役職", placeholder="例: 工場長")
                cert_name = st.text_input("証明者氏名", placeholder="例: 佐藤花子")
            
            if st.button("📄 PDFを生成", type="primary"):
                if all([applicant_name, cert_company, cert_position, cert_name]):
                    success, result = app.generate_pdf(applicant_name, cert_company, cert_name, cert_position)
                    if success:
                        st.success("✅ PDF生成完了！")
                        st.download_button(
                            label="📥 PDFをダウンロード",
                            data=result,
                            file_name=f"公害防止実務証明書_{applicant_name}.pdf",
                            mime="application/pdf"
                        )
                        st.warning("⚠️ 重要: PDFダウンロード後、必ず証明者の印鑑（社印等）を押印してください。")
                    else:
                        st.error(f"エラー: {result}")
                else:
                    st.error("すべての項目を入力してください。")

if __name__ == "__main__":
    main()
