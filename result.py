import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import matplotlib.font_manager as fm

# 配置参数
FONT_PATH = None  # 初始设为None，会自动查找系统中文字体
AVATAR_DIR = "avatars"  # 头像目录
TEAM_LOGO_DIR = "team_logos"  # 队伍标志目录
OUTPUT_FILE = "predictions_table.png"  # 输出文件

def find_system_chinese_font():
    """自动查找系统中的中文字体"""
    try:
        # 尝试常见的中文字体
        for font in fm.findSystemFonts():
            if 'msyh' in font.lower():  # 微软雅黑
                return font
            if 'simhei' in font.lower():  # 黑体
                return font
            if 'simsun' in font.lower():  # 宋体
                return font
            if 'notosanscjk' in font.lower():  # Noto Sans CJK
                return font
        # 如果没找到，返回第一个字体
        return fm.findSystemFonts()[0]
    except:
        return None

def generate_table_visualization(csv_path):
    # 读取CSV数据
    df = pd.read_csv(csv_path)
    
    # 获取标准答案（第一行）
    standard_answers = df.iloc[0, 1:].tolist()
    
    # 移除第一行（标准答案）
    df = df.iloc[1:]
    
    num_matches = 4  # 假设有4场比赛
    num_players = len(df)
    
    # 计算每个玩家的正确场次并添加到DataFrame中
    correct_counts = []
    for _, row in df.iterrows():
        matches = [row[f'第{i}场赛'] for i in range(1, num_matches + 1)]
        correct_count = sum(1 for i in range(num_matches) if matches[i] == standard_answers[i])
        correct_counts.append(correct_count)
    
    df['正确场次'] = correct_counts
    
    # 按正确场次从高到低排序
    df = df.sort_values(by='正确场次', ascending=False).reset_index(drop=True)
    
    # 设置字体 - 优先使用系统中文字体
    global FONT_PATH
    if FONT_PATH is None:
        FONT_PATH = find_system_chinese_font()
    
    try:
        font_large = ImageFont.truetype(FONT_PATH, 28) if FONT_PATH else ImageFont.load_default(28)
        font_medium = ImageFont.truetype(FONT_PATH, 22) if FONT_PATH else ImageFont.load_default(22)
        font_small = ImageFont.truetype(FONT_PATH, 18) if FONT_PATH else ImageFont.load_default(18)
    except:
        # 如果字体加载失败，使用默认字体并调整大小
        default_font = ImageFont.load_default()
        font_large = default_font.font_variant(size=28)
        font_medium = default_font.font_variant(size=22)
        font_small = default_font.font_variant(size=18)
    
    # 表格尺寸参数
    header_height = 120
    row_height = 120
    avatar_col_width = 150
    match_col_width = 180
    result_col_width = 100  # 新增的正确场次列宽度
    border_width = 2
    
    # 计算总图片尺寸 (增加一列用于显示正确场次)
    img_width = avatar_col_width + num_matches * match_col_width + result_col_width
    img_height = header_height + num_players * row_height
    
    # 创建画布
    img = Image.new('RGB', (img_width, img_height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # 绘制表头背景
    draw.rectangle([0, 0, img_width, header_height], fill=(70, 130, 180), outline=(50, 50, 50))
    
    # 绘制标题 - 确保中文显示
    title = "预测结果表"
    bbox = draw.textbbox((0, 0), title, font=font_large)
    title_width = bbox[2] - bbox[0]
    title_height = bbox[3] - bbox[1]
    draw.text((img_width//2 - title_width//2, 20), title, fill=(255, 255, 255), font=font_large)
    
    # 计算表头第二行的高度和位置
    header_row2_height = header_height - 60  # 标题占据60像素
    header_row2_y = 60  # 第二行从60像素开始
    
    # 绘制表头 - 玩家列
    draw.rectangle([0, header_row2_y, avatar_col_width, header_height], fill=(100, 150, 200), outline=(50, 50, 50))
    
    # 玩家列标题
    player_text = "玩家"
    bbox = draw.textbbox((0, 0), player_text, font=font_medium)
    player_text_width = bbox[2] - bbox[0]
    player_text_height = bbox[3] - bbox[1]
    draw.text((avatar_col_width//2 - player_text_width//2, 
               header_row2_y + (header_row2_height - player_text_height)//2), 
              player_text, fill=(255, 255, 255), font=font_medium)
    
    # 绘制表头 - 比赛列
    for i in range(num_matches):
        x_start = avatar_col_width + i * match_col_width
        x_end = x_start + match_col_width
        
        # 比赛列背景
        draw.rectangle([x_start, header_row2_y, x_end, header_height], fill=(100, 150, 200), outline=(50, 50, 50))
        
        # 比赛标题 - 使用中文数字
        chinese_numbers = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
        match_num = chinese_numbers[i] if i < len(chinese_numbers) else str(i+1)
        match_title = f"第{match_num}场"
        
        # 计算文本位置
        bbox = draw.textbbox((0, 0), match_title, font=font_medium)
        match_title_width = bbox[2] - bbox[0]
        match_title_height = bbox[3] - bbox[1]
        
        # 图标大小和间距设置
        logo_size = 25
        spacing = 8  # 图标和文字之间的间距
        
        # 计算总宽度(左图标+间距+文字+间距+右图标)
        total_width = logo_size + spacing + match_title_width + spacing + logo_size
        
        # 计算起始位置(居中)
        start_x = x_start + (match_col_width - total_width) // 2
        
        # 加载并绘制队伍标志
        try:
            # 左图标
            left_logo = Image.open(os.path.join(TEAM_LOGO_DIR, f"match{i+1}_left.png"))
            left_logo = left_logo.resize((logo_size, logo_size))
            img.paste(left_logo, (start_x, 
                                header_row2_y + (header_row2_height - logo_size)//2))
            
            # 文字
            draw.text((start_x + logo_size + spacing, 
                      header_row2_y + (header_row2_height - match_title_height)//2), 
                     match_title, fill=(255, 255, 255), font=font_medium)
            
            # 右图标
            right_logo = Image.open(os.path.join(TEAM_LOGO_DIR, f"match{i+1}_right.png"))
            right_logo = right_logo.resize((logo_size, logo_size))
            img.paste(right_logo, (start_x + logo_size + spacing + match_title_width + spacing, 
                                 header_row2_y + (header_row2_height - logo_size)//2))
        except:
            # 如果图标加载失败，只绘制文字
            draw.text((x_start + (match_col_width - match_title_width) // 2, 
                      header_row2_y + (header_row2_height - match_title_height) // 2), 
                     match_title, fill=(255, 255, 255), font=font_medium)
    
    # 绘制表头 - 正确场次列
    x_start = avatar_col_width + num_matches * match_col_width
    x_end = x_start + result_col_width
    draw.rectangle([x_start, header_row2_y, x_end, header_height], fill=(100, 150, 200), outline=(50, 50, 50))
    
    # 正确场次列标题
    result_text = "正确场次"
    bbox = draw.textbbox((0, 0), result_text, font=font_medium)
    result_text_width = bbox[2] - bbox[0]
    result_text_height = bbox[3] - bbox[1]
    draw.text((x_start + result_col_width//2 - result_text_width//2, 
               header_row2_y + (header_row2_height - result_text_height)//2), 
              result_text, fill=(255, 255, 255), font=font_medium)
    
    # 绘制表格内容
    for row_idx, (_, row) in enumerate(df.iterrows()):
        nickname = row['昵称']
        matches = [row[f'第{i}场赛'] for i in range(1, num_matches + 1)]
        correct_count = row['正确场次']
        y_start = header_height + row_idx * row_height
        y_end = y_start + row_height
        
        # 绘制行背景 (交替颜色)
        row_color = (220, 220, 220) if row_idx % 2 == 0 else (255, 255, 255)
        draw.rectangle([0, y_start, img_width, y_end], fill=row_color, outline=(150, 150, 150))
        
        # 绘制垂直分割线
        for i in range(num_matches + 2):  # 增加一条线用于正确场次列
            x = avatar_col_width + i * match_col_width if i <= num_matches else avatar_col_width + num_matches * match_col_width
            draw.line([x, y_start, x, y_end], fill=(150, 150, 150), width=border_width)
        
        # 绘制水平分割线
        draw.line([0, y_end, img_width, y_end], fill=(150, 150, 150), width=border_width)
        
        # 绘制头像
        try:
            avatar = Image.open(os.path.join(AVATAR_DIR, f"{nickname}.png"))
            avatar = avatar.resize((80, 80))
            img.paste(avatar, (avatar_col_width//2 - 40, y_start + 20))
        except:
            draw.rectangle([avatar_col_width//2 - 40, y_start + 20, avatar_col_width//2 + 40, y_start + 100], 
                        outline=(100, 100, 100))
            draw.text((avatar_col_width//2 - 20, y_start + 50), "头像", fill=(100, 100, 100), font=font_small)

        # 绘制昵称 
        bbox = draw.textbbox((0, 0), nickname, font=font_small)
        name_width = bbox[2] - bbox[0]
        name_height = bbox[3] - bbox[1]
        draw.text((avatar_col_width//2 - name_width//2, y_start + 98), 
                nickname, fill=(0, 0, 0), font=font_small)
       
        # 绘制每场比赛的预测选择
        for match_idx, choice in enumerate(matches):
            x_start = avatar_col_width + match_idx * match_col_width
            x_end = x_start + match_col_width
            
            # 确定选择的队伍
            team = "left" if choice == "左" else "right"
            
            # 判断预测是否正确
            is_correct = choice == standard_answers[match_idx]
            highlight_color = (144, 238, 144) if is_correct else (255, 182, 193)  # 正确绿色，错误粉色
            
            # 绘制高亮背景
            draw.rectangle([x_start + border_width, y_start + border_width, 
                          x_end - border_width, y_end - border_width], 
                          fill=highlight_color)
            
            try:
                # 加载并绘制所选队伍的完整图标
                team_logo = Image.open(os.path.join(TEAM_LOGO_DIR, f"match{match_idx+1}_{team}.png"))
                # 调整大小填满格子空间 (保留10像素边距)
                logo_size = min(match_col_width - 20, row_height - 20)
                team_logo = team_logo.resize((logo_size, logo_size))
                img.paste(team_logo, (x_start + match_col_width//2 - logo_size//2, y_start + row_height//2 - logo_size//2))
            except:
                # 如果图标不存在，绘制占位符
                draw.rectangle([x_start + 10, y_start + 10, x_end - 10, y_end - 10], 
                              fill=(200, 200, 200), outline=(150, 150, 150))
                bbox = draw.textbbox((0, 0), choice, font=font_medium)
                choice_width = bbox[2] - bbox[0]
                draw.text((x_start + match_col_width//2 - choice_width//2, y_start + row_height//2 - 10), 
                         choice, fill=(0, 0, 0), font=font_medium)
        
        # 绘制正确场次数
        x_start = avatar_col_width + num_matches * match_col_width
        x_end = x_start + result_col_width
        
        # 绘制背景
        draw.rectangle([x_start, y_start, x_end, y_end], fill=row_color, outline=(150, 150, 150))
        
        # 绘制数字
        count_text = str(correct_count)
        bbox = draw.textbbox((0, 0), count_text, font=font_medium)
        count_width = bbox[2] - bbox[0]
        count_height = bbox[3] - bbox[1]
        draw.text((x_start + result_col_width//2 - count_width//2, 
                  y_start + row_height//2 - count_height//2), 
                 count_text, fill=(0, 0, 0), font=font_medium)
    
    # 保存图片
    img.save(OUTPUT_FILE)
    print(f"已生成表格化预测图: {OUTPUT_FILE}")

# 使用示例
generate_table_visualization("result.csv")