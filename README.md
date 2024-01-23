# PDF简历解析与简历检索

## 程序主入口
main.py

## 运行方法

1. 配置简历文件目录
    修改config.py中的base_dir目录，该目录存储着所有的pdf版简历文件
2. 解析简历文件
    python main.py 1  # 该程序与函数为解析base_dir下的所有目录文件
3. 检索简历文件
    python main.py 2 sci,ccf  # 该程序与函数为检索base_dir目录下的所有与关键词相关的简历，关键词必须不少于1个，使用半角逗号分隔；