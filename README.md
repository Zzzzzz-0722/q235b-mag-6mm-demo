# Q235B 6 mm MAG 工艺决策模型

这是可独立部署的 Streamlit 演示包。使用 8 条有来源的参数资料进行规则检索，不进行机器学习训练；Q235B 实测训练样本为 0。输入板厚、接头形式、保护气和根部间隙后，页面列出匹配来源的焊丝直径、电流、电压、焊速及道次。OTC 厂家记录属于正反面各焊一道的双面焊参考，不能当作单面单道结果。单 V 形典型案例的原文母材为 SS400，坡口角度 60°，不代表 Q235B 已验证。

## Streamlit Community Cloud

将本目录中的所有文件上传到独立的 GitHub 仓库根目录。在 Streamlit Community Cloud 创建应用时，选择该仓库，并将 Main file path 设为 `q235b_model/app.py`。应用启动后会读取根目录的 `Q235B_MAG_6mm_参数资料库_V0.3.xlsx`。

仓库若设为公开，代码和参数资料库也会公开。请在发布前确认适合向外共享。

## 本地预览

```powershell
python -m pip install -r requirements.txt
python -m streamlit run q235b_model/app.py
```
