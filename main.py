import os
import sys
import pandas as pd
import numpy as np
from glob import glob
import PyPDF2
from tqdm import tqdm
import re
from config import base_dir
from config import pdf_extract_file
from config import pdf_keyword_file
from config import config_keyword_file
import shutil


def extract_pdf_text(pdf_path):

	pdfObj = PyPDF2.PdfReader(pdf_path)
	page_count = len(pdfObj.pages)

	#提取文本
	pdf_rlt = []
	for p in range(0, page_count):
		text = pdfObj.pages[p]
		page_text = text.extract_text()
		page_txts = page_text.strip().split("\n")
		page_txts = [v.strip() for v in page_txts if len(v.strip()) > 3 and not v.strip().isdigit()]
		pdf_rlt.extend(page_txts)
	# for ind, txt in enumerate(pdf_rlt):
	#   print(ind,' ',txt)
	return pdf_rlt


def extract_phone(txt):
	p = '1\d{10}'
	txt = txt.strip().replace('-','').replace(' ','')
	match = re.findall(p,txt)
	if len(match) > 0:
		return match[0]
	else:
		return ''


def extract_email(txt):
	p = '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
	match = re.findall(p,txt)
	if len(match) > 0:
		return match[0]
	else:
		return ''


def extract_name(txt):
	txt = re.sub('【.*?】', '', txt)
	txt = txt.strip()
	name = txt.strip().split(" ")[0]
	return name


def extract_pdf_info():
	glob_files = glob("{}/**/*pdf".format(base_dir), recursive=True)
	pdf_infos = []
	for tmp_pdf in tqdm(glob_files):
		pdf_name = tmp_pdf.strip().split("/")[-1]
		pdf_rlt = extract_pdf_text(tmp_pdf)
		rlt_txt = "|".join(pdf_rlt)
		per_name = extract_name(pdf_name)
		per_tel = extract_phone(rlt_txt)
		per_email = extract_email(rlt_txt)
		pdf_infos.append([per_name, per_tel, per_email, pdf_name, tmp_pdf, rlt_txt])
	pd_infos = pd.DataFrame(pdf_infos, columns=['per_name', 'per_phone', 'per_email', 'pdf_name', 'pdf_path', 'pdf_content'])
	pd_infos.to_csv(pdf_extract_file, index=None, sep=',')


def keyword_match(match_p):
	"""keyword match"""
	dst_dir = './tmp'
	if os.path.isdir(dst_dir):
		shutil.rmtree(dst_dir)
	os.makedirs(dst_dir)
	match_p = match_p.strip().lower()
	pd_infos = pd.read_csv(pdf_extract_file, sep=',')

	rlt = []
	for ind, row in pd_infos.iterrows():
		row_arr = row.tolist()
		row_txt = row['pdf_content'].strip().lower()
		match_labels = re.findall(match_p, row_txt.lower())
		if match_labels:
			match_labels = list(set(match_labels))
			match_labels.sort()
			label = ",".join(match_labels)
			if len(match_labels) > 1:
				print(label, row['per_name'], row['pdf_path'])
				pdf_name = row['pdf_name']
				shutil.copy(row['pdf_path'], os.path.join(dst_dir, pdf_name))

		




if __name__ == "__main__":
	if len(sys.argv) > 1:
		command = sys.argv[1]
		if command in [2,'2']:
			try:
				word_str = sys.argv[2]
			except Exception as e:
				raise ValueError('Usage:\n python parser_pdf.py 1 \n调用extract_pdf_info\n python parser_pdf.py 2 大模型,chatglm \n调用 keyword_match')
	else:
		raise ValueError('Usage:\n python parser_pdf.py 1 \n调用extract_pdf_info\n python parser_pdf.py 2 大模型,chatglm \n调用 keyword_match')

	if command.strip() in [1,'1']:
		# 1. extract pdf info
		extract_pdf_info()
	elif command.strip() in [2,'2']:
		# 2. keyword match
		word_arr = word_str.strip().split(",")
		word_arr = [v.strip() for v in word_arr if len(v.strip()) > 1]
		sort_word_arr = sorted(word_arr,key = lambda x:len(x),reverse = True)
		match_p = "|".join(sort_word_arr)
		keyword_match(match_p)
