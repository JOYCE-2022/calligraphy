#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
书法作品OCR识别与自动命名工具
使用 EasyOCR 进行文字识别
"""

import json
import os
import re
from pathlib import Path

# 诗词数据库（常见诗词）
POEM_DATABASE = {
    "床前明月光": {"title": "静夜思", "author": "李白"},
    "疑是地上霜": {"title": "静夜思", "author": "李白"},
    "举头望明月": {"title": "静夜思", "author": "李白"},
    "低头思故乡": {"title": "静夜思", "author": "李白"},
    "白日依山尽": {"title": "登鹳雀楼", "author": "王之涣"},
    "黄河入海流": {"title": "登鹳雀楼", "author": "王之涣"},
    "欲穷千里目": {"title": "登鹳雀楼", "author": "王之涣"},
    "更上一层楼": {"title": "登鹳雀楼", "author": "王之涣"},
    "春眠不觉晓": {"title": "春晓", "author": "孟浩然"},
    "处处闻啼鸟": {"title": "春晓", "author": "孟浩然"},
    "夜来风雨声": {"title": "春晓", "author": "孟浩然"},
    "花落知多少": {"title": "春晓", "author": "孟浩然"},
    "锄禾日当午": {"title": "悯农", "author": "李绅"},
    "汗滴禾下土": {"title": "悯农", "author": "李绅"},
    "谁知盘中餐": {"title": "悯农", "author": "李绅"},
    "粒粒皆辛苦": {"title": "悯农", "author": "李绅"},
    "离离原上草": {"title": "赋得古原草送别", "author": "白居易"},
    "一岁一枯荣": {"title": "赋得古原草送别", "author": "白居易"},
    "野火烧不尽": {"title": "赋得古原草送别", "author": "白居易"},
    "春风吹又生": {"title": "赋得古原草送别", "author": "白居易"},
    "鹅鹅鹅": {"title": "咏鹅", "author": "骆宾王"},
    "曲项向天歌": {"title": "咏鹅", "author": "骆宾王"},
    "白毛浮绿水": {"title": "咏鹅", "author": "骆宾王"},
    "红掌拨清波": {"title": "咏鹅", "author": "骆宾王"},
    "日照香炉生紫烟": {"title": "望庐山瀑布", "author": "李白"},
    "遥看瀑布挂前川": {"title": "望庐山瀑布", "author": "李白"},
    "飞流直下三千尺": {"title": "望庐山瀑布", "author": "李白"},
    "疑是银河落九天": {"title": "望庐山瀑布", "author": "李白"},
    "两个黄鹂鸣翠柳": {"title": "绝句", "author": "杜甫"},
    "一行白鹭上青天": {"title": "绝句", "author": "杜甫"},
    "窗含西岭千秋雪": {"title": "绝句", "author": "杜甫"},
    "门泊东吴万里船": {"title": "绝句", "author": "杜甫"},
    "远看山有色": {"title": "画", "author": "王维"},
    "近听水无声": {"title": "画", "author": "王维"},
    "春去花还在": {"title": "画", "author": "王维"},
    "人来鸟不惊": {"title": "画", "author": "王维"},
    "一去二三里": {"title": "山村咏怀", "author": "邵康节"},
    "烟村四五家": {"title": "山村咏怀", "author": "邵康节"},
    "亭台六七座": {"title": "山村咏怀", "author": "邵康节"},
    "八九十枝花": {"title": "山村咏怀", "author": "邵康节"},
    "解落三秋叶": {"title": "风", "author": "李峤"},
    "能开二月花": {"title": "风", "author": "李峤"},
    "过江千尺浪": {"title": "风", "author": "李峤"},
    "入竹万竿斜": {"title": "风", "author": "李峤"},
    "众鸟高飞尽": {"title": "独坐敬亭山", "author": "李白"},
    "孤云独去闲": {"title": "独坐敬亭山", "author": "李白"},
    "相看两不厌": {"title": "独坐敬亭山", "author": "李白"},
    "只有敬亭山": {"title": "独坐敬亭山", "author": "李白"},
    "松下问童子": {"title": "寻隐者不遇", "author": "贾岛"},
    "言师采药去": {"title": "寻隐者不遇", "author": "贾岛"},
    "只在此山中": {"title": "寻隐者不遇", "author": "贾岛"},
    "云深不知处": {"title": "寻隐者不遇", "author": "贾岛"},
    "千山鸟飞绝": {"title": "江雪", "author": "柳宗元"},
    "万径人踪灭": {"title": "江雪", "author": "柳宗元"},
    "孤舟蓑笠翁": {"title": "江雪", "author": "柳宗元"},
    "独钓寒江雪": {"title": "江雪", "author": "柳宗元"},
    "墙角数枝梅": {"title": "梅花", "author": "王安石"},
    "凌寒独自开": {"title": "梅花", "author": "王安石"},
    "遥知不是雪": {"title": "梅花", "author": "王安石"},
    "为有暗香来": {"title": "梅花", "author": "王安石"},
    "泉眼无声惜细流": {"title": "小池", "author": "杨万里"},
    "树阴照水爱晴柔": {"title": "小池", "author": "杨万里"},
    "小荷才露尖尖角": {"title": "小池", "author": "杨万里"},
    "早有蜻蜓立上头": {"title": "小池", "author": "杨万里"},
    "碧玉妆成一树高": {"title": "咏柳", "author": "贺知章"},
    "万条垂下绿丝绦": {"title": "咏柳", "author": "贺知章"},
    "不知细叶谁裁出": {"title": "咏柳", "author": "贺知章"},
    "二月春风似剪刀": {"title": "咏柳", "author": "贺知章"},
    "天地玄黄": {"title": "千字文", "author": "周兴嗣"},
    "宇宙洪荒": {"title": "千字文", "author": "周兴嗣"},
    "人之初": {"title": "三字经", "author": "王应麟"},
    "性本善": {"title": "三字经", "author": "王应麟"},
    "横平竖直": {"title": "书法练习", "author": ""},
    "永字八法": {"title": "永字八法", "author": ""},
    "上善若水": {"title": "上善若水", "author": "老子"},
    "厚德载物": {"title": "厚德载物", "author": "《周易》"},
    "宁静致远": {"title": "宁静致远", "author": "诸葛亮"},
    "淡泊明志": {"title": "淡泊明志", "author": "诸葛亮"},
    "海纳百川": {"title": "海纳百川", "author": "林则徐"},
    "有容乃大": {"title": "海纳百川", "author": "林则徐"},
}

class ArtworkTitleGenerator:
    def __init__(self):
        self.data_file = "data/artworks.json"
        self.images_dir = "images"
        self.ocr = None
        
    def init_ocr(self):
        """初始化 EasyOCR"""
        if self.ocr is None:
            print("正在加载 EasyOCR 模型...")
            import easyocr
            # 使用中文简体模型
            self.ocr = easyocr.Reader(['ch_sim'], gpu=False, verbose=False)
            print("✅ EasyOCR 加载完成\n")
        return self.ocr
        
    def load_artworks(self):
        """加载作品数据"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_artworks(self, data):
        """保存作品数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def ocr_image(self, image_path):
        """
        使用 EasyOCR 识别图片文字
        按照中国书法从右到左、从上到下的顺序排列
        """
        ocr = self.init_ocr()
        
        try:
            result = ocr.readtext(image_path)
            
            if result:
                # 提取文字及其位置
                text_items = []
                for detection in result:
                    bbox = detection[0]  # 边界框坐标 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                    text = detection[1]  # 文字内容
                    confidence = detection[2]  # 置信度
                    
                    if confidence > 0.3:
                        # 计算文字中心点
                        center_x = sum(p[0] for p in bbox) / 4
                        center_y = sum(p[1] for p in bbox) / 4
                        text_items.append({
                            'text': text,
                            'x': center_x,
                            'y': center_y,
                            'confidence': confidence
                        })
                
                if not text_items:
                    return {'success': False, 'text': '', 'error': '未识别到文字'}
                
                # 按照中国书法顺序排列：从右到左（x降序），从上到下（y升序）
                # 先按列分组（x坐标相近的归为一列）
                text_items.sort(key=lambda t: -t['x'])  # 先按x降序（从右到左）
                
                # 判断是否为竖排文字（高度大于宽度的情况）
                all_x = [t['x'] for t in text_items]
                all_y = [t['y'] for t in text_items]
                x_range = max(all_x) - min(all_x) if all_x else 0
                y_range = max(all_y) - min(all_y) if all_y else 0
                
                if y_range > x_range * 0.5:  # 可能是竖排
                    # 按列分组，然后每列从上到下排序
                    columns = []
                    col_threshold = x_range / max(len(text_items), 1) * 1.5 if x_range > 0 else 50
                    
                    for item in text_items:
                        placed = False
                        for col in columns:
                            if abs(item['x'] - col[0]['x']) < col_threshold:
                                col.append(item)
                                placed = True
                                break
                        if not placed:
                            columns.append([item])
                    
                    # 每列按y升序排列（从上到下）
                    for col in columns:
                        col.sort(key=lambda t: t['y'])
                    
                    # 列按x降序排列（从右到左）
                    columns.sort(key=lambda col: -col[0]['x'])
                    
                    # 合并文字
                    texts = []
                    for col in columns:
                        for item in col:
                            texts.append(item['text'])
                else:
                    # 横排文字，从右到左
                    text_items.sort(key=lambda t: (-t['y'], -t['x']))
                    texts = [item['text'] for item in text_items]
                
                full_text = ''.join(texts)
                return {
                    'success': bool(full_text),
                    'text': full_text,
                    'lines': texts
                }
            else:
                return {
                    'success': False,
                    'text': '',
                    'error': '未识别到文字'
                }
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'error': str(e)
            }
    
    def search_poem_source(self, text):
        """
        查找诗词来源
        """
        if not text:
            return {'found': False}
        
        # 清理文字
        clean_text = re.sub(r'[，。！？、；：\s]', '', text)
        
        # 在数据库中查找匹配
        for key, info in POEM_DATABASE.items():
            clean_key = re.sub(r'[，。！？、；：\s]', '', key)
            if clean_key in clean_text or clean_text in clean_key:
                return {
                    'found': True,
                    'title': info['title'],
                    'author': info['author']
                }
        
        return {'found': False}
    
    def generate_title(self, text):
        """
        根据识别的文字生成标题
        """
        if not text:
            return "未命名作品"
        
        # 查找诗词来源
        poem_info = self.search_poem_source(text)
        
        if poem_info['found']:
            return poem_info['title']
        else:
            # 使用第一句话作为标题
            # 清理文字，按标点分割
            clean_text = text.strip()
            for punct in '，。！？；：、\n':
                clean_text = clean_text.split(punct)[0]
            
            # 限制长度
            if len(clean_text) > 10:
                clean_text = clean_text[:10]
            
            return clean_text if clean_text else "未命名作品"
    
    def process_batch_ocr(self):
        """
        批量OCR识别模式
        """
        data = self.load_artworks()
        artworks = data['artworks']
        
        print("=" * 60)
        print("  书法作品标题生成工具 - EasyOCR 自动识别")
        print("=" * 60)
        print()
        
        updated_count = 0
        
        for i, artwork in enumerate(artworks):
            filename = artwork['filename']
            image_path = os.path.join(self.images_dir, filename)
            
            print(f"[{i+1}/{len(artworks)}] {filename}")
            print(f"  日期: {artwork['date_display']}")
            
            if not os.path.exists(image_path):
                print(f"  ❌ 文件不存在")
                continue
            
            # OCR 识别
            result = self.ocr_image(image_path)
            
            if result['success'] and result['text']:
                text = result['text']
                print(f"  识别内容: {text[:30]}{'...' if len(text) > 30 else ''}")
                
                # 生成标题
                title = self.generate_title(text)
                artwork['title'] = title
                artwork['content'] = text
                
                # 查找诗词来源
                poem_info = self.search_poem_source(text)
                if poem_info['found']:
                    artwork['poem_source'] = poem_info
                    print(f"  ✅ 标题: {title} (来源: {poem_info.get('author', '')})")
                else:
                    print(f"  ✅ 标题: {title}")
                
                updated_count += 1
            else:
                print(f"  ⚠️ 识别失败: {result.get('error', '未知错误')}")
                artwork['title'] = "未命名作品"
            
            print()
        
        # 保存更新
        self.save_artworks(data)
        print("=" * 60)
        print(f"✅ 完成！已处理 {len(artworks)} 幅作品，成功识别 {updated_count} 幅")
        print(f"📁 数据已保存到: {self.data_file}")
        print("=" * 60)

def main():
    generator = ArtworkTitleGenerator()
    generator.process_batch_ocr()

if __name__ == '__main__':
    main()
