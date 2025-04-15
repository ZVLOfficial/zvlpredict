import csv
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import matplotlib.font_manager as fm

# 配置参数
FONT_PATH = None  # 初始设为None，会自动查找系统中文字体
AVATAR_DIR = "avatars"  # 头像目录
TEAM_LOGO_DIR = "team_logos"  # 队伍标志目录
BACKGROUND_DIR = "background"  # 背景图目录
OUTPUT_CSV = "output.csv"  # 中间CSV文件名
OUTPUT_IMAGE = "predictions_table.png"  # 输出图片文件名

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

def process_predictions(input_file):
    """处理原始预测数据并生成中间CSV文件"""
    # 读取输入CSV文件
    with open(input_file, mode='r', encoding='utf-8') as infile:
        csv_reader = csv.reader(infile)
        
        # 获取标题行
        headers = next(csv_reader)
        
        # 确定比赛列的范围（从第3列开始）
        match_columns = headers[3:]
        num_matches = len(match_columns)
        
        # 准备结果列表
        results = []
        
        for row in csv_reader:
            nickname = row[2]  # 第3列是昵称
            
            # 处理每场比赛预测
            predictions = []
            for i in range(num_matches):
                prediction = row[3 + i]  # 从第4列开始是比赛预测
                
                # 处理预测结果
                if '右边赢' in prediction or '右' in prediction:
                    pred = '右'
                elif '左边赢' in prediction or '左' in prediction:
                    pred = '左'
                else:
                    # 解析比分
                    scores = prediction.split('：')
                    if len(scores) == 2:
                        left, right = scores
                        pred = '左' if int(left) > int(right) else '右'
                    else:
                        pred = '未知'
                
                predictions.append(pred)
            
            # 添加到结果列表 [昵称, 预测1, 预测2, ...]
            results.append([nickname] + predictions)
    
    # 写入输出CSV文件
    with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as outfile:
        csv_writer = csv.writer(outfile)
        
        # 写入标题行
        header = ['昵称'] + [f'第{i+1}场赛' for i in range(num_matches)]
        csv_writer.writerow(header)
        
        # 写入数据行
        csv_writer.writerows(results)
    
    print(f"预测数据处理完成！中间结果已保存到 {OUTPUT_CSV}")
    return num_matches  # 返回比赛数量

def generate_table_visualization(num_matches):
    """根据中间CSV文件生成可视化表格图片"""
    # 读取CSV数据
    df = pd.read_csv(OUTPUT_CSV)
    num_players = len(df)
    
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
    
    # 表格尺寸参数（调整后的布局）
    header_height = 250  # 增加表头高度
    row_height = 150  # 增加行高
    avatar_col_width = 180  # 增加头像列宽度
    match_col_width = 220  # 增加比赛列宽度（从200增加到220）
    side_margin = 10  # 左右边距各10像素
    team_logo_spacing = 5  # 同一场比赛两个队伍标志之间的间距（从10减少到5）
    match_col_spacing = 0  # 不同比赛列之间的间距（增加间距）
    
    # 计算总图片尺寸（增加左右边距）
    img_width = side_margin * 2 + avatar_col_width + num_matches * match_col_width + (num_matches - 1) * match_col_spacing
    img_height = header_height + num_players * row_height + 100  # 增加底部额外空间
    
    # 创建透明背景
    img = Image.new('RGBA', (img_width, img_height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        # 加载头部背景图
        head_bg = Image.open(os.path.join(BACKGROUND_DIR, "head.png"))
        # 调整头部背景图宽度以匹配表格尺寸
        head_bg = head_bg.resize((img_width, header_height))  # 使用新的header_height
        
        # 加载底部背景图
        foot_bg = Image.open(os.path.join(BACKGROUND_DIR, "foot.png"))
        # 计算底部背景图需要的高度
        foot_height = img_height - header_height  # 总高度减去头部高度
        # 调整底部背景图尺寸
        foot_bg = foot_bg.resize((img_width, foot_height))
        
        # 将头部背景图粘贴到顶部
        img.paste(head_bg, (0, 0))
        # 将底部背景图粘贴到头部下方
        img.paste(foot_bg, (0, header_height))
        
    except Exception as e:
        print(f"背景图加载失败: {e}")
        # 如果背景图加载失败，保持透明背景
    
    # 绘制标题 - 确保中文显示
    title = ""
    bbox = draw.textbbox((0, 0), title, font=font_large)
    title_width = bbox[2] - bbox[0]
    title_height = bbox[3] - bbox[1]
    draw.text((img_width//2 - title_width//2, 30), title, fill=(255, 255, 255), font=font_large)
    
    # 计算表头第二行的高度和位置
    header_row2_height = 100  # 固定第二行高度
    header_row2_y = header_height - header_row2_height - 20  # 从header_height减去第二行高度和额外空间
    
    # 玩家列标题（添加左边距）
    player_text = " "
    bbox = draw.textbbox((0, 0), player_text, font=font_medium)
    player_text_width = bbox[2] - bbox[0]
    player_text_height = bbox[3] - bbox[1]
    draw.text((side_margin + avatar_col_width//2 - player_text_width//2, 
               header_row2_y + (header_row2_height - player_text_height)//2), 
              player_text, fill=(255, 255, 255), font=font_medium)
    
    # 绘制表头 - 比赛列
    for i in range(num_matches):
        x_start = side_margin + avatar_col_width + i * (match_col_width + match_col_spacing)
        
        # 图标大小设置 - 保持原始比例
        logo_size = 80  # 固定大小
        
        try:
            # 左图标 - 保持原始比例
            left_logo = Image.open(os.path.join(TEAM_LOGO_DIR, f"match{i+1}_left.png"))
            # 计算保持比例的缩放
            left_ratio = min(logo_size / left_logo.width, logo_size / left_logo.height)
            left_new_width = int(left_logo.width * left_ratio)
            left_new_height = int(left_logo.height * left_ratio)
            left_logo = left_logo.resize((left_new_width, left_new_height))
            
            # 右图标 - 保持原始比例
            right_logo = Image.open(os.path.join(TEAM_LOGO_DIR, f"match{i+1}_right.png"))
            right_ratio = min(logo_size / right_logo.width, logo_size / right_logo.height)
            right_new_width = int(right_logo.width * right_ratio)
            right_new_height = int(right_logo.height * right_ratio)
            right_logo = right_logo.resize((right_new_width, right_new_height))
            
            # 计算总宽度和起始位置（使用更小的team_logo_spacing）
            total_width = left_new_width + right_new_width + team_logo_spacing
            start_x = x_start + (match_col_width - total_width) // 2
            
            # 粘贴左图标
            img.paste(left_logo, (start_x, 
                                header_row2_y + (header_row2_height - left_new_height)//2), left_logo)
            
            # 粘贴右图标（使用更小的team_logo_spacing）
            img.paste(right_logo, (start_x + left_new_width + team_logo_spacing, 
                                header_row2_y + (header_row2_height - right_new_height)//2), right_logo)
        except Exception as e:
            print(f"队伍标志加载失败: {e}")
            # 如果图标加载失败，只绘制文字
            match_title = f"比赛 {i+1}"
            bbox = draw.textbbox((0, 0), match_title, font=font_medium)
            match_title_width = bbox[2] - bbox[0]
            match_title_height = bbox[3] - bbox[1]
            draw.text((x_start + (match_col_width - match_title_width) // 2, 
                      header_row2_y + (header_row2_height - match_title_height) // 2), 
                     match_title, fill=(255, 255, 255), font=font_medium)
    
    # 绘制表格内容
    for row_idx, (_, row) in enumerate(df.iterrows()):
        nickname = row['昵称']
        matches = [row[f'第{i+1}场赛'] for i in range(num_matches)]
        y_start = header_height + row_idx * row_height
        
        # 绘制头像（添加左边距）
        try:
            avatar = Image.open(os.path.join(AVATAR_DIR, f"{nickname}.png"))
            # 保持头像比例
            avatar_ratio = min(80 / avatar.width, 80 / avatar.height)
            avatar_new_width = int(avatar.width * avatar_ratio)
            avatar_new_height = int(avatar.height * avatar_ratio)
            avatar = avatar.resize((avatar_new_width, avatar_new_height))
            # 使用alpha通道确保透明背景
            if avatar.mode != 'RGBA':
                avatar = avatar.convert('RGBA')
            img.paste(avatar, (side_margin + avatar_col_width//2 - avatar_new_width//2, 
                              y_start + 20), avatar)
        except Exception as e:
            print(f"头像加载失败: {e}")
            # 如果头像加载失败，绘制透明占位符
            pass

        # 绘制昵称 （添加左边距）
        bbox = draw.textbbox((0, 0), nickname, font=font_small)
        name_width = bbox[2] - bbox[0]
        name_height = bbox[3] - bbox[1]
        draw.text((side_margin + avatar_col_width//2 - name_width//2, y_start + 110),  # 在头像下方预留足够空间
                nickname, fill=(255, 255, 255), font=font_small)
       
        # 绘制每场比赛的预测选择
        for match_idx, choice in enumerate(matches):
            x_start = side_margin + avatar_col_width + match_idx * (match_col_width + match_col_spacing)
            
            # 确定选择的队伍
            team = "left" if choice == "左" else "right"
            
            try:
                # 加载并绘制所选队伍的完整图标
                team_logo = Image.open(os.path.join(TEAM_LOGO_DIR, f"match{match_idx+1}_{team}.png"))
                # 保持原始比例缩放
                logo_size = 100  # 固定大小
                logo_ratio = min(logo_size / team_logo.width, logo_size / team_logo.height)
                logo_new_width = int(team_logo.width * logo_ratio)
                logo_new_height = int(team_logo.height * logo_ratio)
                team_logo = team_logo.resize((logo_new_width, logo_new_height))
                # 使用alpha通道确保透明背景
                if team_logo.mode != 'RGBA':
                    team_logo = team_logo.convert('RGBA')
                img.paste(team_logo, (x_start + match_col_width//2 - logo_new_width//2, 
                                     y_start + row_height//2 - logo_new_height//2), team_logo)
            except Exception as e:
                print(f"预测队伍标志加载失败: {e}")
                # 如果图标不存在，只绘制文字
                bbox = draw.textbbox((0, 0), choice, font=font_medium)
                choice_width = bbox[2] - bbox[0]
                choice_height = bbox[3] - bbox[1]
                draw.text((x_start + match_col_width//2 - choice_width//2, 
                          y_start + row_height//2 - choice_height//2), 
                         choice, fill=(255, 255, 255), font=font_medium)
    
    # 保存图片
    img.save(OUTPUT_IMAGE)
    print(f"已生成透明背景的预测图: {OUTPUT_IMAGE}")

def main(input_file):
    """主函数，处理整个流程"""
    # 第一步：处理原始预测数据
    num_matches = process_predictions(input_file)
    
    # 第二步：生成可视化表格
    generate_table_visualization(num_matches)
    
    print("所有处理完成！")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("请指定输入文件: python script.py input.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    main(input_file)