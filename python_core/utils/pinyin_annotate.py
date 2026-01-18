import zipfile
import os
from bs4 import BeautifulSoup, NavigableString, Comment, Doctype, ProcessingInstruction, Declaration
import traceback
import re

try:
    from utils.log import logwriter
except ImportError:
    from log import logwriter

logger = logwriter()

# Try to import pypinyin, provide helpful error if not available
try:
    from pypinyin import pinyin, Style
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False
    logger.write("警告: pypinyin 库未安装，无法进行拼音注音。请运行: pip install pypinyin")

class PinyinAnnotate:
    def __init__(self, epub_path, output_path):
        if not os.path.exists(epub_path):
            raise Exception("EPUB文件不存在")

        self.epub_path = os.path.normpath(epub_path)
        self.epub = zipfile.ZipFile(epub_path)
        
        if output_path and os.path.exists(output_path):
            if os.path.isfile(output_path):
                raise Exception("输出路径不能是文件")
        else:
            output_path = os.path.dirname(epub_path)
            
        self.output_path = os.path.normpath(output_path)
        self.file_write_path = os.path.join(
            self.output_path,
            os.path.basename(self.epub_path).replace(".epub", "_pinyin.epub"),
        )
        
        if os.path.exists(self.file_write_path):
            os.remove(self.file_write_path)
            
        self.target_epub = zipfile.ZipFile(
            self.file_write_path,
            "w",
            zipfile.ZIP_DEFLATED,
        )
        
        # 汉字正则表达式（基本汉字范围）
        self.hanzi_pattern = re.compile(r'[\u4e00-\u9fff]+')

    def add_pinyin_to_text(self, text):
        """给文本中的汉字添加拼音注音"""
        if not text or not PYPINYIN_AVAILABLE:
            return text
            
        # 查找所有汉字序列
        parts = []
        last_end = 0
        
        for match in self.hanzi_pattern.finditer(text):
            # 添加非汉字部分
            if match.start() > last_end:
                parts.append(text[last_end:match.start()])
            
            # 处理汉字部分
            hanzi_text = match.group()
            try:
                # 获取每个汉字的拼音（不带声调）
                pinyin_list = pinyin(hanzi_text, style=Style.NORMAL)
                
                # 构建ruby标签
                ruby_parts = []
                for hz, py in zip(hanzi_text, pinyin_list):
                    ruby_parts.append(f'<ruby>{hz}<rt>{py[0]}</rt></ruby>')
                
                parts.append(''.join(ruby_parts))
            except Exception as e:
                # 如果拼音转换失败，保留原汉字
                logger.write(f"拼音转换失败 '{hanzi_text}': {e}")
                parts.append(hanzi_text)
            
            last_end = match.end()
        
        # 添加剩余部分
        if last_end < len(text):
            parts.append(text[last_end:])
        
        return ''.join(parts)

    def process_file(self):
        """处理EPUB文件中的所有HTML/XML文件"""
        if not PYPINYIN_AVAILABLE:
            raise Exception("pypinyin库未安装，无法进行拼音注音。请安装: pip install pypinyin")
        
        for item in self.epub.infolist():
            content = self.epub.read(item.filename)
            
            # 处理HTML/XHTML/NCX/OPF文件
            if item.filename.lower().endswith(('.html', '.xhtml', '.htm', '.ncx', '.opf')):
                try:
                    # 尝试检测编码，epub通常使用utf-8
                    text_content = content.decode('utf-8')
                    
                    # 使用BeautifulSoup处理HTML文件以避免破坏标签
                    if item.filename.lower().endswith(('.html', '.xhtml', '.htm')):
                        soup = BeautifulSoup(text_content, 'html.parser')
                        
                        # 转换文本节点
                        for string in soup.find_all(string=True):
                            # 跳过特殊标签（注释、文档类型、处理指令等）
                            if isinstance(string, (Comment, Doctype, ProcessingInstruction, Declaration)):
                                continue
                                
                            # 跳过样式和脚本标签
                            if string.parent.name not in ['style', 'script']:
                                new_string = self.add_pinyin_to_text(string)
                                string.replace_with(new_string)
                                
                        # 转换标签中的title和alt属性
                        for tag in soup.find_all(True):
                            if tag.has_attr('title'):
                                tag['title'] = self.add_pinyin_to_text(tag['title'])
                            if tag.has_attr('alt'):
                                tag['alt'] = self.add_pinyin_to_text(tag['alt'])
                                
                        # 返回处理后的HTML
                        new_content = str(soup).encode('utf-8')
                        
                    else:
                        # 处理NCX/OPF文件
                        soup = BeautifulSoup(text_content, 'xml')
                        
                        # 转换标签中的文本
                        for string in soup.find_all(string=True):
                            # 跳过特殊标签
                            if isinstance(string, (Comment, Doctype, ProcessingInstruction, Declaration)):
                                continue
                                
                            new_string = self.add_pinyin_to_text(string)
                            string.replace_with(new_string)
                            
                        new_content = str(soup).encode('utf-8')

                    self.target_epub.writestr(item.filename, new_content)
                    
                except Exception as e:
                    logger.write(f"文件 {item.filename} 处理失败，使用原内容: {e}")
                    self.target_epub.writestr(item, content)
            else:
                # 复制其他文件（图片、CSS、字体等）
                self.target_epub.writestr(item, content)

        self.close_file()
        # Return tuple compatible with cli.py handling
        return 0, self.file_write_path

    def close_file(self):
        """关闭ZIP文件"""
        if self.epub:
            self.epub.close()
        if self.target_epub:
            self.target_epub.close()

    def fail_del_target(self):
        """失败时删除目标文件"""
        if self.file_write_path and os.path.exists(self.file_write_path):
            os.remove(self.file_write_path)
            logger.write(f"删除临时文件: {self.file_write_path}")

def run_add_pinyin(epub_path, output_path=None):
    """运行拼音注音功能的主函数"""
    logger.write(f"\n正在尝试给EPUB添加拼音注音: {epub_path}")
    
    if not PYPINYIN_AVAILABLE:
        error_msg = "错误: pypinyin库未安装。请运行: pip install pypinyin"
        logger.write(error_msg)
        return (1, error_msg)
    
    pinyin_tool = None
    try:
        pinyin_tool = PinyinAnnotate(epub_path, output_path)
        result = pinyin_tool.process_file()
        return result
    except Exception as e:
        error_msg = f"拼音注音失败: {e}"
        logger.write(error_msg)
        traceback.print_exc()
        if pinyin_tool:
            pinyin_tool.close_file()
            pinyin_tool.fail_del_target()
        return (1, error_msg)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        epub_read_path = sys.argv[1]
        run_add_pinyin(epub_read_path)
