COURSE_BLUEPRINT = {
    "title": "走进人工智能",
    "description": (
        "面向初中阶段的人工智能专题学习课程，围绕概念认知、工作原理、伦理安全与未来趋势展开，"
        "并配套实践体验、在线答题、资源拓展、社区交流和学习数据反馈。"
    ),
    "chapter_title": "走进人工智能专题学习",
    "chapter_description": "按照 4 个课时组织课程学习、实践体验、资源拓展与学习评价。",
}

STUDENT_FEEDBACK_BLUEPRINT = {
    "title": "初中人工智能单元学习自评问卷",
    "subtitle": "适用于“走进人工智能”单元第 1-4 课完整学习后使用。",
    "sections": [
        {"title": "一、基本信息", "fields": ["student_name", "class_name"]},
        {"title": "二、知识掌握自评（单选）", "fields": ["knowledge_q1", "knowledge_q2", "knowledge_q3", "knowledge_q4"]},
        {"title": "三、实践能力自评（单选）", "fields": ["practice_q5", "practice_q6", "practice_q7"]},
        {"title": "四、学习态度与参与度（单选）", "fields": ["attitude_q8", "attitude_q9", "attitude_q10"]},
        {"title": "五、综合反思（简答）", "fields": ["reflection_gain", "reflection_gap", "reflection_advice"]},
        {"title": "六、综合等级", "fields": ["overall_level"]},
    ],
}

LESSON_PAGE_DATA = {
    1: {
        "title": "认识人工智能",
        "full_title": "第一课时 认识人工智能",
        "estimated_minutes": 45,
        "video_url": "https://www.bilibili.com/video/BV1CY411H7oZ?t=159.2",
        "attachment_url": "https://www.bilibili.com/video/BV1CY411H7oZ?t=159.2",
        "hero_summary": "围绕人工智能的定义、四大特征与发展历史建立基础认知，并通过语音识别和图像识别体验感受 AI 的感知能力。",
        "content": "学习目标：理解人工智能的基本概念、四大特征与发展脉络，能够结合生活案例初步判断人工智能的典型能力。",
        "structure_flow": "课堂目标 → 微课学习 → 什么是人工智能 → 人工智能四大特征 → 发展历史年表 → 实践体验 → 课堂练习 → 社区任务",
        "sections": [
            {
                "type": "video",
                "eyebrow": "微课学习",
                "title": "微课学习",
                "videos": [
                    {
                        "title": "《什么是人工智能》",
                        "task": "视频中介绍了人工智能的哪些功能？人工智能有哪些基本特点？请认真观看并思考。",
                        "url": "https://www.bilibili.com/video/BV1CY411H7oZ?t=159.2",
                    }
                ],
            },
            {
                "type": "text",
                "eyebrow": "核心知识",
                "title": "什么是人工智能",
                "paragraphs": [
                    "人工智能（英文缩写：AI），是指由人类制造的机器，能够模拟、延伸和扩展人类智能，让机器具备像人一样看、听、说、学习、思考、推理的能力。"
                ],
            },
            {
                "type": "feature_grid",
                "eyebrow": "核心知识",
                "title": "人工智能四大特征",
                "items": [
                    {"icon": "👀", "title": "感知能力", "lead": "AI 的眼睛、耳朵、皮肤", "body": "定义：人工智能通过图像、声音、文字等方式感知世界的能力。", "detail": "生活例子：人脸识别、语音识别、拍照识物。"},
                    {"icon": "💬", "title": "语言理解能力", "lead": "AI 能听会说、读懂文字", "body": "定义：人工智能能够听懂、读懂人类语言，并进行交流、回答、翻译的能力。", "detail": "生活例子：智能语音助手、AI 聊天、机器翻译。"},
                    {"icon": "📚", "title": "学习能力", "lead": "AI 越学越聪明", "body": "定义：人工智能从大量数据中学习规律，不断优化自身，越用越准确的能力。", "detail": "生活例子：个性化推荐、人脸解锁越来越精准。"},
                    {"icon": "🧠", "title": "推理能力", "lead": "AI 会思考、做判断", "body": "定义：人工智能根据已有信息进行分析、判断、决策的能力。", "detail": "生活例子：AI 下棋、智能路线规划、逻辑判断。"},
                ],
            },
            {
                "type": "timeline",
                "eyebrow": "发展脉络",
                "title": "人工智能发展历史大事年表",
                "groups": [
                    {"label": "萌芽期（1936-1955）", "events": ["1936 图灵提出图灵机", "1943 提出神经元 MP 模型", "1946 第一台电子计算机 ENIAC 诞生", "1950 图灵提出图灵测试"]},
                    {"label": "初创期（1956-1980）", "events": ["1956 达特茅斯会议，人工智能正式诞生", "1958 提出感知机模型", "1966 第一个智能聊天机器人 ELIZA", "1969 第一个可移动机器人 Shakey"]},
                    {"label": "成长期（1981-2011）", "events": ["1986 提出反向传播算法", "1997 深蓝战胜国际象棋世界冠军", "2006 辛顿提出深度学习理论", "2011 IBM Watson 战胜人类冠军"]},
                    {"label": "第三次热潮（2012-至今）", "events": ["2012 AlexNet 推动深度学习快速发展", "2016 AlphaGo 战胜围棋世界冠军", "2017 Transformer 模型诞生", "2022 ChatGPT 等大模型出现"]},
                ],
            },
            {
                "type": "action_cards",
                "eyebrow": "实践体验",
                "title": "实践体验：感受 AI 感知能力",
                "intro": "先完成语音识别与图像识别体验，再思考：这体现了人工智能的什么能力？",
                "items": [
                    {"title": "语音识别体验", "points": ["进入实践体验模块，使用语音识别功能。", "朗读一句完整的话，观察 AI 是否能准确转换成文字。", "思考：这体现了人工智能的什么能力？"], "buttons": [{"label": "进入语音识别", "route": "practice:speech_lab"}]},
                    {"title": "图像识别体验", "points": ["进入实践体验模块，使用图像识别功能。", "上传一张清晰图片，观察 AI 能否识别出图片中的物体。", "思考：这体现了人工智能的什么能力？"], "buttons": [{"label": "进入图像识别", "route": "practice:image_lab"}]},
                ],
            },
            {
                "type": "exercise",
                "eyebrow": "课堂练习",
                "title": "课堂练习",
                "questions": [
                    {"stem": "人工智能的英文缩写是（）", "options": [{"key": "A", "text": "IT"}, {"key": "B", "text": "AI"}, {"key": "C", "text": "IP"}, {"key": "D", "text": "OS"}], "answer": "B", "explanation": "Artificial Intelligence 的常用英文缩写是 AI。"},
                    {"stem": "人工智能正式诞生的标志是（）", "options": [{"key": "A", "text": "图灵测试"}, {"key": "B", "text": "达特茅斯会议"}, {"key": "C", "text": "ENIAC"}, {"key": "D", "text": "深蓝"}], "answer": "B", "explanation": "1956 年达特茅斯会议被普遍视为人工智能正式诞生的标志。"},
                    {"stem": "1950 年图灵提出的测试是（）", "options": [{"key": "A", "text": "神经元模型"}, {"key": "B", "text": "图灵测试"}, {"key": "C", "text": "控制论"}, {"key": "D", "text": "感知机"}], "answer": "B", "explanation": "图灵测试用于判断机器是否具备类似人的智能表现。"},
                    {"stem": "世界上第一台电子计算机是（）", "options": [{"key": "A", "text": "ENIAC"}, {"key": "B", "text": "IBM704"}, {"key": "C", "text": "AlexNet"}, {"key": "D", "text": "AlphaGo"}], "answer": "A", "explanation": "ENIAC 是早期电子计算机的重要代表。"},
                    {"stem": "下列属于 AI 感知能力的是（）", "options": [{"key": "A", "text": "人脸识别"}, {"key": "B", "text": "写作文"}, {"key": "C", "text": "推理"}, {"key": "D", "text": "学习优化"}], "answer": "A", "explanation": "人脸识别通过图像理解来感知外界，属于 AI 感知能力。"},
                    {"stem": "2016 年战胜围棋冠军的 AI 是（）", "options": [{"key": "A", "text": "深蓝"}, {"key": "B", "text": "Watson"}, {"key": "C", "text": "AlphaGo"}, {"key": "D", "text": "ChatGPT"}], "answer": "C", "explanation": "AlphaGo 在围棋领域取得了标志性突破。"},
                    {"stem": "1997 年战胜国际象棋冠军的是（）", "options": [{"key": "A", "text": "深蓝"}, {"key": "B", "text": "AlphaZero"}, {"key": "C", "text": "GPT-3"}, {"key": "D", "text": "Sora"}], "answer": "A", "explanation": "深蓝战胜国际象棋世界冠军是 AI 历史上的经典事件。"},
                    {"stem": "AI 越用越准确，体现的是（）", "options": [{"key": "A", "text": "感知能力"}, {"key": "B", "text": "语言能力"}, {"key": "C", "text": "学习能力"}, {"key": "D", "text": "推理能力"}], "answer": "C", "explanation": "通过不断学习数据而持续优化，体现的是学习能力。"},
                    {"stem": "推动深度学习爆发的模型是（）", "options": [{"key": "A", "text": "LeNet-5"}, {"key": "B", "text": "AlexNet"}, {"key": "C", "text": "Transformer"}, {"key": "D", "text": "GAN"}], "answer": "B", "explanation": "AlexNet 在图像识别中的突破推动了深度学习热潮。"},
                    {"stem": "下列属于语言理解能力的是（）", "options": [{"key": "A", "text": "语音对话"}, {"key": "B", "text": "图像识别"}, {"key": "C", "text": "自动驾驶"}, {"key": "D", "text": "数据计算"}], "answer": "A", "explanation": "语音对话需要理解并生成语言，属于语言理解能力。"},
                ],
            },
            {
                "type": "action_cards",
                "eyebrow": "社区任务",
                "title": "课后社区任务：发布“我身边的 AI”观察笔记",
                "items": [
                    {
                        "title": "社区观察任务",
                        "points": [
                            "在学习社区发布“我身边的 AI”观察笔记。",
                            "说明该 AI 属于什么类型、应用在什么场景、带来了什么实际价值。",
                        ],
                        "buttons": [
                            {"label": "前往发布观察笔记", "route": "forum:note_create", "lesson_query": True},
                            {"label": "浏览本课笔记", "route": "forum:note_list", "lesson_filter": True},
                        ],
                    }
                ],
            },
        ],
    },
    2: {
        "title": "人工智能如何工作",
        "full_title": "第二课时 人工智能如何工作",
        "estimated_minutes": 45,
        "video_url": "https://www.bilibili.com/video/BV1mgPvzTEvb?t=316.4",
        "attachment_url": "https://www.bilibili.com/video/BV1Er421773P?t=25.2",
        "hero_summary": "理解人工智能依靠数据、算法、算力三大要素运行，并结合多行业案例观察 AI 的落地方式。",
        "content": "学习目标：理解数据、算法、算力三大要素的含义和作用，能够结合典型场景解释人工智能如何完成任务。",
        "structure_flow": "微课学习 → 人工智能三大要素 → 三要素对照表 → 应用领域视频 → 应用案例 → 实践体验 → 课堂练习 → 社区拓展",
        "sections": [
            {
                "type": "video",
                "eyebrow": "微课学习",
                "title": "微课学习",
                "videos": [
                    {"title": "《AI 是如何工作的》", "task": "微课中使用了什么类比来解释人工智能的学习过程？请记录下来。", "url": "https://www.bilibili.com/video/BV1mgPvzTEvb?t=316.4"}
                ],
            },
            {
                "type": "feature_grid",
                "eyebrow": "核心知识",
                "title": "人工智能三大要素",
                "items": [
                    {"icon": "🗂️", "title": "数据", "lead": "AI 学习的素材与经验", "body": "定义：数据是人工智能学习所使用的信息、素材、经验与案例，是 AI 学习的基础。", "detail": "作用与类比：为人工智能提供学习经验，数据越多、质量越高，AI 越智能；相当于课本、例题和生活经验。"},
                    {"icon": "⚙️", "title": "算法", "lead": "AI 学习与思考的方法", "body": "定义：算法是人工智能学习、处理信息、分析问题、做出判断的规则、步骤和方法。", "detail": "作用与类比：决定人工智能如何学习、如何思考、如何输出结果；相当于学习方法、解题思路和思考方式。"},
                    {"icon": "💻", "title": "算力", "lead": "AI 运行所需的硬件能力", "body": "定义：算力是支持人工智能运行的硬件计算能力、处理速度与支撑条件。", "detail": "作用与类比：保证人工智能快速处理海量数据、完成复杂任务；相当于体力、反应速度和大脑处理能力。"},
                ],
            },
            {"type": "table", "eyebrow": "核心知识", "title": "三大要素对照表", "headers": ["要素", "定义", "核心作用", "学习类比"], "rows": [["数据", "AI 学习的信息、素材、经验", "提供学习基础", "课本、例题、生活经验"], ["算法", "AI 学习与推理的规则方法", "决定学习方式", "学习方法、解题思路"], ["算力", "AI 运行的计算速度与能力", "保证运行效率", "体力、大脑处理速度"]]},
            {
                "type": "video",
                "eyebrow": "应用拓展",
                "title": "人工智能应用领域",
                "videos": [
                    {"title": "《人工智能在不同领域的应用》", "task": "记录人工智能在医疗、金融、交通、教育四个领域的应用案例。这些应用分别用到了人工智能的什么能力？", "url": "https://www.bilibili.com/video/BV1Er421773P?t=25.2"}
                ],
            },
            {"type": "case_grid", "eyebrow": "应用拓展", "title": "人工智能应用领域", "items": [{"title": "医疗", "points": ["辅助诊断", "病灶影像识别", "医疗影像分析"]}, {"title": "金融", "points": ["风险评估", "智能客服", "量化预测"]}, {"title": "交通", "points": ["自动驾驶", "智能导航", "路线规划"]}, {"title": "教育", "points": ["个性化学习推荐", "智能辅导", "作业批改"]}], "note": "思考：这些应用分别用到了人工智能的什么能力？"},
            {
                "type": "action_cards",
                "eyebrow": "实践体验",
                "title": "实践体验：与 AI 对话",
                "intro": "围绕“你是怎么学会回答问题的？你需要什么才能回答问题？”与 AI 进行一次完整对话。",
                "items": [
                    {"title": "AI 智能对话体验", "points": ["进入实践体验模块，使用 AI 对话功能。", "可以提问：你是怎么学会回答问题的？你需要什么才能回答问题？", "总结：人工智能依靠数据、算法、算力三大要素协同工作。"], "buttons": [{"label": "进入 AI 对话", "route": "practice:dialogue_lab"}]}
                ],
            },
            {
                "type": "exercise",
                "eyebrow": "课堂练习",
                "title": "课堂练习",
                "questions": [
                    {"stem": "人工智能工作的三大核心要素是（）", "options": [{"key": "A", "text": "数据、算法、算力"}, {"key": "B", "text": "软件、硬件、网络"}, {"key": "C", "text": "语音、图像、文字"}, {"key": "D", "text": "输入、处理、输出"}], "answer": "A", "explanation": "数据、算法、算力共同构成人工智能运行的三大核心要素。"},
                    {"stem": "在人工智能中，被称为机器学习“经验”的是（）", "options": [{"key": "A", "text": "算法"}, {"key": "B", "text": "数据"}, {"key": "C", "text": "算力"}, {"key": "D", "text": "模型"}], "answer": "B", "explanation": "数据为模型提供经验与样本，是机器学习的基础。"},
                    {"stem": "人工智能中，负责“告诉机器怎么学习”的是（）", "options": [{"key": "A", "text": "数据"}, {"key": "B", "text": "算法"}, {"key": "C", "text": "算力"}, {"key": "D", "text": "接口"}], "answer": "B", "explanation": "算法决定机器如何处理信息、学习规律并输出结果。"},
                    {"stem": "支撑人工智能高速运行的计算能力与硬件基础被称为（）", "options": [{"key": "A", "text": "数据"}, {"key": "B", "text": "算法"}, {"key": "C", "text": "算力"}, {"key": "D", "text": "网络"}], "answer": "C", "explanation": "算力负责支撑人工智能快速运行和复杂计算。"},
                    {"stem": "下列属于人工智能在交通领域应用的是（）", "options": [{"key": "A", "text": "智能阅卷"}, {"key": "B", "text": "自动驾驶"}, {"key": "C", "text": "远程问诊"}, {"key": "D", "text": "量化交易"}], "answer": "B", "explanation": "自动驾驶是人工智能在交通领域的典型应用。"},
                    {"stem": "下列属于人工智能在医疗领域应用的是（）", "options": [{"key": "A", "text": "人脸识别支付"}, {"key": "B", "text": "病灶影像识别"}, {"key": "C", "text": "智能推荐网课"}, {"key": "D", "text": "股票预测"}], "answer": "B", "explanation": "病灶影像识别是人工智能在医疗领域的重要应用场景。"},
                    {"stem": "下列属于人工智能在教育领域应用的是（）", "options": [{"key": "A", "text": "智能导航"}, {"key": "B", "text": "个性化学习推荐"}, {"key": "C", "text": "金融风控"}, {"key": "D", "text": "安防监控"}], "answer": "B", "explanation": "个性化学习推荐体现了人工智能在教育场景中的应用价值。"},
                    {"stem": "我们用 AI 对话时，AI 能理解并回答问题，主要依靠的是（）", "options": [{"key": "A", "text": "只有数据"}, {"key": "B", "text": "只有算力"}, {"key": "C", "text": "数据 + 算法 + 算力协同"}, {"key": "D", "text": "人工后台回复"}], "answer": "C", "explanation": "AI 对话依赖数据、算法和算力协同完成理解与生成。"},
                    {"stem": "下列对数据、算法、算力关系描述正确的是（）", "options": [{"key": "A", "text": "有数据就够了，算法和算力不重要"}, {"key": "B", "text": "算力越强，不需要数据和算法"}, {"key": "C", "text": "三者相互独立，互不影响"}, {"key": "D", "text": "数据是燃料，算法是引擎，算力是基础"}], "answer": "D", "explanation": "数据、算法和算力需要协同工作，三者缺一不可。"},
                    {"stem": "下列不属于人工智能典型应用领域的是（）", "options": [{"key": "A", "text": "金融"}, {"key": "B", "text": "交通"}, {"key": "C", "text": "教育"}, {"key": "D", "text": "纯手工雕刻"}], "answer": "D", "explanation": "纯手工雕刻不是人工智能的典型应用领域。"},
                ],
            },
            {
                "type": "action_cards",
                "eyebrow": "社区拓展",
                "title": "课后社区拓展",
                "items": [
                    {
                        "title": "分享 AI 应用观察",
                        "points": [
                            "在社区分享：“你觉得 AI 最厉害的应用是什么？为什么？”",
                            "可以结合医疗、金融、交通、教育中的一个具体案例说明理由。",
                        ],
                        "buttons": [
                            {"label": "前往社区发帖", "route": "forum:post_create", "lesson_query": True},
                            {"label": "浏览本课讨论", "route": "forum:post_list", "lesson_filter": True},
                        ],
                    }
                ],
            },
        ],
    },
    3: {
        "title": "人工智能伦理与安全",
        "full_title": "第三课时 人工智能伦理与安全",
        "estimated_minutes": 45,
        "video_url": "https://www.bilibili.com/video/BV1Az421m7Wc?t=173.1",
        "attachment_url": "https://www.bilibili.com/video/BV1Az421m7Wc?t=173.1",
        "hero_summary": "从隐私安全、就业冲击与深度伪造等案例切入，理解 AI 既能带来便利，也会带来新的伦理与安全挑战。",
        "content": "学习目标：认识人工智能可能带来的伦理和安全问题，形成理性看待、合理利用、守规则的技术使用意识。",
        "structure_flow": "微课学习 → 人工智能三大伦理问题 → 课堂活动：社区辩论 → 课堂练习",
        "sections": [
            {"type": "video", "eyebrow": "微课学习", "title": "微课学习", "videos": [{"title": "《人工智能的伦理问题》", "task": "视频中提到了哪三个人工智能伦理问题？请记录下来。", "url": "https://www.bilibili.com/video/BV1Az421m7Wc?t=173.1"}]},
            {"type": "case_grid", "eyebrow": "核心知识", "title": "人工智能三大伦理问题", "items": [{"title": "就业冲击", "points": ["可能被替代：重复性高、规则简单的工作。", "新增岗位：AI 训练师、算法工程师、AI 安全专家。", "观点：AI 替代的是工作方式，不是劳动者本身。"]}, {"title": "隐私安全", "points": ["风险：个人信息泄露、滥用、未经授权收集。", "保护方法：不随意授权、不泄露验证码、保护人脸与声音信息。"]}, {"title": "诈骗与深度伪造", "points": ["手段：AI 换脸、语音克隆、伪造音视频。", "防范：不轻信、不转账、多方核实、提高警惕。"]}]},
            {
                "type": "action_cards",
                "eyebrow": "课堂活动",
                "title": "课堂活动：社区辩论",
                "intro": "围绕“人工智能的发展是利大于弊还是弊大于利？”展开观点发布与回复互动。",
                "items": [
                    {"title": "发布观点", "points": ["在社区发布自己的观点并说明理由。", "可以从效率提升、隐私安全、就业变化等角度组织论证。"], "buttons": [{"label": "前往发布讨论", "route": "forum:post_create", "lesson_query": True}, {"label": "进入社区讨论", "route": "forum:post_list", "lesson_filter": True}]},
                    {"title": "回复他人观点", "points": ["阅读同学发布的观点，尝试提出补充、质疑或回应。", "形成讨论链，训练理性表达和证据支撑能力。"], "buttons": [{"label": "浏览本课讨论", "route": "forum:post_list", "lesson_filter": True}]},
                ],
            },
            {
                "type": "exercise",
                "eyebrow": "课堂练习",
                "title": "课堂练习",
                "questions": [
                    {"stem": "下列哪一项不属于人工智能带来的伦理问题（）", "options": [{"key": "A", "text": "隐私泄露"}, {"key": "B", "text": "就业冲击"}, {"key": "C", "text": "深度伪造"}, {"key": "D", "text": "提高学习效率"}], "answer": "D", "explanation": "提高学习效率通常是积极影响，不属于伦理风险本身。"},
                    {"stem": "利用 AI 伪造他人声音、面部进行诈骗的技术叫做（）", "options": [{"key": "A", "text": "语音识别"}, {"key": "B", "text": "深度伪造"}, {"key": "C", "text": "图像识别"}, {"key": "D", "text": "机器翻译"}], "answer": "B", "explanation": "深度伪造会利用 AI 技术伪造声音、图像或视频内容。"},
                    {"stem": "面对 AI 语音克隆诈骗，最正确的做法是（）", "options": [{"key": "A", "text": "直接转账"}, {"key": "B", "text": "多方核实，不轻易转账"}, {"key": "C", "text": "相信对方所说"}, {"key": "D", "text": "随便告诉对方验证码"}], "answer": "B", "explanation": "面对可疑信息时，最重要的是核实身份并谨慎处理。"},
                    {"stem": "下列哪种工作最不容易被 AI 替代（）", "options": [{"key": "A", "text": "流水线工人"}, {"key": "B", "text": "数据录入员"}, {"key": "C", "text": "创意设计师"}, {"key": "D", "text": "简单客服"}], "answer": "C", "explanation": "创意、综合判断和人类情感沟通类工作更难被完全替代。"},
                    {"stem": "保护个人隐私，不正确的做法是（）", "options": [{"key": "A", "text": "不随意授权 APP 权限"}, {"key": "B", "text": "不随便上传人脸、声音信息"}, {"key": "C", "text": "随意告诉他人验证码"}, {"key": "D", "text": "谨慎填写个人信息"}], "answer": "C", "explanation": "验证码属于敏感信息，泄露会带来较大风险。"},
                    {"stem": "AI 时代新增的职业是（）", "options": [{"key": "A", "text": "打字员"}, {"key": "B", "text": "AI 训练师"}, {"key": "C", "text": "传统售票员"}, {"key": "D", "text": "流水线工人"}], "answer": "B", "explanation": "AI 训练师是随着人工智能发展新增的重要岗位。"},
                    {"stem": "我们应该如何看待人工智能的发展（）", "options": [{"key": "A", "text": "只看好处，无视风险"}, {"key": "B", "text": "只看坏处，拒绝使用"}, {"key": "C", "text": "理性看待，合理利用"}, {"key": "D", "text": "完全依赖人工智能"}], "answer": "C", "explanation": "面对新技术，需要在理解价值的同时重视风险防范。"},
                    {"stem": "下列不属于深度伪造的是（）", "options": [{"key": "A", "text": "AI 换脸视频"}, {"key": "B", "text": "语音克隆"}, {"key": "C", "text": "真实拍摄的视频"}, {"key": "D", "text": "伪造他人声音"}], "answer": "C", "explanation": "真实拍摄的视频不属于 AI 深度伪造内容。"},
                    {"stem": "个人数据被滥用，主要侵犯了我们的（）", "options": [{"key": "A", "text": "财产权"}, {"key": "B", "text": "隐私权"}, {"key": "C", "text": "著作权"}, {"key": "D", "text": "肖像权"}], "answer": "B", "explanation": "个人数据被滥用最直接侵犯的是隐私权。"},
                    {"stem": "使用人工智能最重要的原则是（）", "options": [{"key": "A", "text": "合法、安全、守伦理"}, {"key": "B", "text": "可以随意使用他人信息"}, {"key": "C", "text": "能用就行，不管风险"}, {"key": "D", "text": "可以用来欺骗他人"}], "answer": "A", "explanation": "合法、安全、符合伦理是使用人工智能的基本底线。"},
                ],
            },
        ],
    },
    4: {
        "title": "人工智能的未来与单元总结",
        "full_title": "第四课时 人工智能的未来与单元总结",
        "estimated_minutes": 45,
        "video_url": "https://www.bilibili.com/video/BV1vs421N7pf?t=161.4",
        "attachment_url": "https://www.bilibili.com/video/BV1vs421N7pf?t=161.4",
        "hero_summary": "展望人工智能未来发展趋势，完成单元自评与课堂总结，形成对“概念、原理、伦理、未来”的完整认识。",
        "content": "学习目标：了解人工智能的未来发展方向，完成在线自评与课堂总结，形成完整的单元学习闭环。",
        "structure_flow": "课堂导入 → 微课学习 → 人工智能未来发展趋势 → 单元自评与总结 → 课堂总结 → 单元综合练习",
        "sections": [
            {"type": "list", "eyebrow": "课堂导入", "title": "课堂导入", "points": ["未来的人工智能还能为学习、生活和工作做些什么？", "未来人工智能可能带来哪些新的风险和挑战？"]},
            {"type": "video", "eyebrow": "微课学习", "title": "微课学习", "videos": [{"title": "《人工智能的未来发展趋势》", "task": "视频中提到了三个人工智能未来发展方向，请记录下来。", "url": "https://www.bilibili.com/video/BV1vs421N7pf?t=161.4"}]},
            {"type": "feature_grid", "eyebrow": "新知学习", "title": "人工智能未来发展趋势", "note": "思考问题：这些未来趋势对学习、生活和工作意味着什么？", "items": [{"icon": "🚀", "title": "更智能", "lead": "理解与推理能力继续增强", "body": "理解能力、推理能力更强，能处理更复杂任务。", "detail": "意味着 AI 会在更多真实场景中承担复杂辅助工作。"}, {"icon": "🌐", "title": "更通用", "lead": "一个 AI 处理多类任务", "body": "一个 AI 可完成多种任务，适应更多场景。", "detail": "未来的 AI 会更像综合型学习伙伴和工作助手。"}, {"icon": "🛡️", "title": "更安全可信", "lead": "更加重视伦理与治理", "body": "更加注重伦理、隐私保护和风险控制。", "detail": "未来 AI 的发展必须建立在安全、可信和可治理的基础上。"}, {"icon": "🤝", "title": "更普惠", "lead": "更多普通人可直接受益", "body": "走进教育、医疗、家庭，人人可用。", "detail": "人工智能会进入更多日常场景，服务更广泛的人群。"}]},
            {
                "type": "action_cards",
                "eyebrow": "单元反思",
                "title": "单元自评与总结",
                "intro": "完成在线自评问卷，系统回顾四个课时的知识掌握、实践能力、学习投入与综合反思。",
                "items": [
                    {"title": "在线自评问卷", "points": ["完成“走进人工智能”单元学习自评问卷。", "内容包括：知识掌握、实践能力、学习态度与参与度、综合反思、综合等级。", "提交后可在数据看板查看自己的学习反思记录。"], "buttons": [{"label": "进入数据看板", "route": "analytics:index"}]}
                ],
            },
            {"type": "list", "eyebrow": "课堂总结", "title": "课堂总结", "points": ["AI 是服务人类的工具，要善用、安全用、合理用。", "保持好奇心，做负责任、有伦理意识的 AI 使用者。"]},
            {
                "type": "exercise",
                "eyebrow": "单元综合练习",
                "title": "单元综合练习",
                "questions": [
                    {"stem": "下列不属于人工智能未来发展趋势的是（）", "options": [{"key": "A", "text": "更智能"}, {"key": "B", "text": "更通用"}, {"key": "C", "text": "更安全可信"}, {"key": "D", "text": "完全取代人类"}], "answer": "D", "explanation": "人工智能的发展强调协作与增强，不等于完全取代人类。"},
                    {"stem": "人工智能的三大核心要素是（）", "options": [{"key": "A", "text": "数据、算法、算力"}, {"key": "B", "text": "手机、电脑、平板"}, {"key": "C", "text": "图像、语音、文字"}, {"key": "D", "text": "识别、对话、翻译"}], "answer": "A", "explanation": "数据、算法和算力共同构成人工智能运行的基础。"},
                    {"stem": "AI 换脸、语音克隆属于（）", "options": [{"key": "A", "text": "深度伪造"}, {"key": "B", "text": "图像识别"}, {"key": "C", "text": "语音识别"}, {"key": "D", "text": "机器翻译"}], "answer": "A", "explanation": "AI 换脸和语音克隆都属于深度伪造场景。"},
                    {"stem": "保护个人隐私不正确的做法是（）", "options": [{"key": "A", "text": "不随意泄露验证码"}, {"key": "B", "text": "不乱上传人脸照片"}, {"key": "C", "text": "随意授权 APP 权限"}, {"key": "D", "text": "谨慎填写个人信息"}], "answer": "C", "explanation": "随意授权权限会增加隐私泄露风险。"},
                    {"stem": "人工智能的英文缩写是（）", "options": [{"key": "A", "text": "AI"}, {"key": "B", "text": "PC"}, {"key": "C", "text": "IP"}, {"key": "D", "text": "TV"}], "answer": "A", "explanation": "Artificial Intelligence 的缩写是 AI。"},
                    {"stem": "AI“越用越准确”主要体现了（）", "options": [{"key": "A", "text": "学习能力"}, {"key": "B", "text": "感知能力"}, {"key": "C", "text": "语言能力"}, {"key": "D", "text": "推理能力"}], "answer": "A", "explanation": "持续根据数据优化结果，体现的是学习能力。"},
                    {"stem": "人工智能正式诞生的标志是（）", "options": [{"key": "A", "text": "图灵测试"}, {"key": "B", "text": "达特茅斯会议"}, {"key": "C", "text": "ENIAC"}, {"key": "D", "text": "AlphaGo"}], "answer": "B", "explanation": "1956 年达特茅斯会议通常被认为是人工智能诞生标志。"},
                    {"stem": "下列属于 AI 感知能力的是（）", "options": [{"key": "A", "text": "人脸识别"}, {"key": "B", "text": "写作文"}, {"key": "C", "text": "逻辑推理"}, {"key": "D", "text": "自主学习"}], "answer": "A", "explanation": "人脸识别依赖视觉感知能力。"},
                    {"stem": "我们应该如何看待 AI（）", "options": [{"key": "A", "text": "只看好处"}, {"key": "B", "text": "只看坏处"}, {"key": "C", "text": "理性看待、合理利用"}, {"key": "D", "text": "完全依赖"}], "answer": "C", "explanation": "面对 AI 应保持理性判断并合理使用。"},
                    {"stem": "未来我们要做怎样的 AI 使用者（）", "options": [{"key": "A", "text": "合法、安全、守伦理"}, {"key": "B", "text": "随意使用他人信息"}, {"key": "C", "text": "用来诈骗"}, {"key": "D", "text": "无视隐私风险"}], "answer": "A", "explanation": "未来 AI 使用者应具备规则意识、伦理意识和安全意识。"},
                ],
            },
        ],
    },
}

COURSE_GLOSSARY = [
    (1, "人工智能", "让机器具备感知、理解、学习、推理和生成能力的一类技术总称。"),
    (2, "感知能力", "人工智能识别图像、声音、文字等外部信息的能力。"),
    (3, "语言理解能力", "人工智能理解并生成自然语言的能力。"),
    (4, "学习能力", "人工智能从数据中总结规律并不断优化结果的能力。"),
    (5, "推理能力", "人工智能根据已有信息进行分析、判断和决策的能力。"),
    (6, "数据", "人工智能学习和训练所依赖的信息、样本和案例。"),
    (7, "算法", "人工智能处理信息、学习规律和做出判断的规则方法。"),
    (8, "算力", "支撑人工智能运行的计算资源、速度与硬件能力。"),
    (9, "深度伪造", "利用 AI 伪造图像、视频、语音等内容的技术。"),
    (10, "隐私保护", "在数据收集、使用和存储过程中保障个人信息安全的要求。"),
    (11, "人机协同", "由人和 AI 各自发挥优势，共同完成任务的协作方式。"),
    (12, "多模态", "同时处理文本、图像、语音、视频等多种信息形式的能力。"),
]

RESOURCE_LIBRARY = [
    {"title": "生活中的人工智能案例阅读", "resource_type": "reading", "lesson_no": 1, "sort_order": 1, "external_url": "https://www.ibm.com/topics/artificial-intelligence", "tags": "案例, 阅读, 第1课", "description": "围绕语音助手、人脸识别、拍照搜题、智能推荐等场景，帮助学生理解生活中的人工智能。"},
    {"title": "人工智能发展简史资料", "resource_type": "reading", "lesson_no": 1, "sort_order": 2, "external_url": "https://en.wikipedia.org/wiki/History_of_artificial_intelligence", "tags": "历史, 阅读, 第1课", "description": "梳理人工智能发展过程中的关键节点，辅助学生理解 AI 发展历史。"},
    {"title": "语音识别、图像识别原理简介", "resource_type": "courseware", "lesson_no": 1, "sort_order": 3, "external_url": "https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API", "tags": "语音识别, 图像识别, 第1课", "description": "用简明图文介绍语音识别与图像识别的基本原理，为实践体验做准备。"},
    {"title": "AI 在各行业应用图文资料", "resource_type": "reading", "lesson_no": 2, "sort_order": 1, "external_url": "https://www.ibm.com/think/topics/artificial-intelligence-use-cases", "tags": "应用, 行业, 第2课", "description": "整理医疗、金融、交通、教育等领域的 AI 应用案例。"},
    {"title": "典型人工智能产品介绍", "resource_type": "reading", "lesson_no": 2, "sort_order": 2, "external_url": "https://www.cloudflare.com/learning/ai/what-is-machine-learning/", "tags": "产品, 第2课", "description": "帮助学生了解常见 AI 产品背后的工作方式和典型能力。"},
    {"title": "AI 对话交互使用说明", "resource_type": "tool", "lesson_no": 2, "sort_order": 3, "external_url": "https://platform.openai.com/docs/guides/text", "tags": "对话, 第2课", "description": "介绍如何围绕数据、算法、算力等知识点开展 AI 对话体验。"},
    {"title": "AI 隐私安全与伦理案例", "resource_type": "reading", "lesson_no": 3, "sort_order": 1, "external_url": "https://www.unesco.org/en/artificial-intelligence/recommendation-ethics", "tags": "伦理, 隐私, 第3课", "description": "聚焦隐私泄露、深度伪造和技术滥用等典型伦理案例。"},
    {"title": "算法公平性阅读材料", "resource_type": "reading", "lesson_no": 3, "sort_order": 2, "external_url": "https://www.ibm.com/think/topics/ai-bias", "tags": "公平性, 第3课", "description": "引导学生认识算法偏见、公平性和责任边界。"},
    {"title": "科技伦理规范说明", "resource_type": "courseware", "lesson_no": 3, "sort_order": 3, "external_url": "https://www.unesco.org/en/artificial-intelligence/recommendation-ethics", "tags": "伦理规范, 第3课", "description": "帮助学生理解合法、安全、守伦理的技术使用原则。"},
    {"title": "人工智能未来发展趋势资料", "resource_type": "reading", "lesson_no": 4, "sort_order": 1, "external_url": "https://education.microsoft.com/zh-cn/resource/ai", "tags": "未来, 第4课", "description": "介绍多模态融合、自主学习、人机协同等人工智能未来趋势。"},
    {"title": "单元知识思维导图", "resource_type": "courseware", "lesson_no": 4, "sort_order": 2, "external_url": "https://www.mindmeister.com/", "tags": "思维导图, 第4课", "description": "用于梳理本单元四个课时的核心知识结构。"},
    {"title": "学习总结与反思模板", "resource_type": "courseware", "lesson_no": 4, "sort_order": 3, "external_url": "https://www.canva.com/presentations/templates/education/", "tags": "总结, 反思, 第4课", "description": "帮助学生完成单元学习总结、成果展示与反思记录。"},
]

GUIDE_BLUEPRINT = {
    "title": "走进人工智能——教学指引",
    "unit_name": "走进人工智能",
    "objectives": (
        "一、适用对象\n"
        "初中 7-9 年级学生\n\n"
        "二、课时安排\n"
        "共 4 课时，每课时 45 分钟\n\n"
        "三、学习目标\n"
        "1. 理解人工智能基本概念与典型应用。\n"
        "2. 能够使用语音识别、图像识别、AI 对话等交互功能。\n"
        "3. 了解人工智能伦理与安全问题，树立正确技术观。\n"
        "4. 能够通过网站完成学习、答题、交流、总结全过程。"
    ),
    "key_points": "课程内容 → 交互体验 → 资源库拓展 → 在线答题检测 → 社区交流分享 → 数据看板查看学习情况",
    "difficult_points": "教学重点在于帮助学生理解 AI 的概念、工作原理、伦理边界和未来趋势，并将知识迁移到实际场景。",
    "learning_methods": (
        "1. 学生按课时顺序依次学习，观看微课视频。\n"
        "2. 每节课完成对应实践体验与练习题。\n"
        "3. 拓展内容可在资源库自主学习。\n"
        "4. 学习心得与成果可发布至社区交流。\n"
        "5. 学习数据可在数据看板查看。"
    ),
    "assignment_suggestion": "建议围绕生活中的 AI 观察、伦理案例辨析、未来趋势畅想和单元总结展示组织作业。",
    "evaluation_suggestion": "课堂评价可结合课时完成度、社区参与度、在线答题结果和单元自评问卷综合观察。",
}

FORUM_DEMO_POSTS = [
    {"title": "我身边的人工智能", "lesson_no": 1, "category": "discussion", "content": "分享自己生活中遇到的 AI 应用，如语音助手、刷脸支付、拍照搜题等，并说明它带来了哪些便利。", "is_pinned": True},
    {"title": "AI 伦理小讨论", "lesson_no": 3, "category": "discussion", "content": "人工智能带来便利的同时，也可能引发隐私安全、深度伪造和就业变化。最需要注意什么问题？", "is_pinned": False},
    {"title": "我的学习总结", "lesson_no": 4, "category": "share", "content": "分享本单元学习收获、体会与反思，梳理对人工智能概念、应用、伦理与未来的理解。", "is_pinned": False},
]

SHOWCASE_DEMO_POSTS = [
    {"title": "成果展示：我理解的人工智能", "lesson_no": 4, "category": "showcase", "content": "从概念、工作原理、伦理风险和未来趋势四个角度整理了本单元学习成果，并结合语音识别和图像识别体验写出展示稿。", "is_pinned": True},
    {"title": "成果展示：AI 应用观察卡", "lesson_no": 4, "category": "showcase", "content": "围绕导航推荐、智能辅导和深度伪造三个案例，归纳了 AI 的价值、风险与责任边界。", "is_pinned": False},
]

LESSON_QUIZ_BANK = {
    lesson_no: next(section["questions"] for section in lesson_data["sections"] if section["type"] == "exercise")
    for lesson_no, lesson_data in LESSON_PAGE_DATA.items()
}
