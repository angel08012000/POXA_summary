from flask import Flask, request, make_response
from datetime import datetime
import io
from web_summary import auto_summary, auto_get_text, auto_get_title

app = Flask(__name__)

@app.route('/summary', methods=['POST'])
def summary():
    data = request.json
    url = data.get('url')

    if not url:
        return {"error": "Missing 'url' parameter"}, 400


    # 生成 MDX 內容
    final_response = auto_summary(auto_get_text(url), *auto_get_title(url))

    # 將內容存到內存中的文件物件
    mdx_file = io.StringIO()
    mdx_file.write(final_response)
    mdx_file.seek(0)

    # 構造 Flask 回應，附帶文件
    response = make_response(mdx_file.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename="{datetime.today().strftime("%Y-%m-%d")}.mdx"'
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'

    return response

if __name__ == '__main__':
    app.run(debug=True)