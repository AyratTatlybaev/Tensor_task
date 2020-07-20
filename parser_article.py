#!/usr/bin/env python3

import urllib.request
import textwrap 
from urllib.parse import urlparse

import re
import sys
import os
import json

#Класс обработки страницы
class myParser:
	'''
	Класс обработки страницы, поиска заголовка статьи и текста статьи.
	'''
	def __init__(self, base_url):
		self.base_url = base_url
		self.html = ''
		self.article_header = ''
		self.article_text = []
		self.article_text_wrap = []
		self.settings = {}
		
	def load(self):
		"""
		Загрузка настроек для форматирования сохраняемого файла
		"""
		#открыть файл с настройками
		try:
			with open('settings.txt', 'r') as f:
				self.settings = json.load(f)
		except FileNotFoundError:
			print('Ошибка! Нет файла настроек.')
			setting = {"file_format": "txt", "text_width": 80}
			with open('settings.txt', 'w') as outfile:
				json.dump(setting, outfile)

	def get_html(self):
		"""
		Получаем страницу html и проверяем ее на кодировку
		"""
		#список предполагаемых кодировок страницы
		encoding = ['utf-8','cp1251']		
		response = ''
		#запрос на получение страницы и её чтение
		try:
			with urllib.request.urlopen(self.base_url) as f:
				response = f.read()
		except urllib.error.URLError as e:
			print('Ошибка чтения страницы: ', e)
			exit()
		#считываем страницу с разными кодировками 
		for encode in encoding:
			try:
				self.html = response.decode(encode)
			except (UnicodeDecodeError, LookupError) as u:
				print('Unicode Error', u)
		

	def get_links(self):
		"""
		Заменяем все ссылки внутри текста на формат "[ссылка]"
		"""
		#текст статьи, отформатированный с учётом формата "[ссылка]"
		new_article_text = []
		#шаблон для поиска тега с ссылкой
		pattern_link = r'(<.*>)?<a href.*>'
		#шаблон для поиска ссылки
		pattern_url  = r'((http(s)?://)|(www\.))[^\s]+/(\w*(\.)?[^"\/]*)?'

		#перебираем текст статьи по параграфам
		for s in self.article_text:
			#ищем в тексте тег с ссылкой по шаблону
			link = re.search(pattern_link,str(s))
			#если тег с ссылкой есть 
			if link != None:
				#ищем ссылку в теге по шаблону
				new_url = re.search(pattern_url, str(link.group(0))) 
				#новый формат ссылки
				new_url_format = " [" + str(new_url.group(0)) + "] "
				#заменяем тег на сыылку в формате "[ссылка]"
				res = s.replace(str(link.group(0)),new_url_format)				
			else:
				#иначе просто записываем параграф без изменений
				res = s
			#удаляем из текста все лищние теги
			res = re.sub(r'(&.{0,5};)*(<[^а-яА-Я.,]+>)*','',res)
			#добавляем форматированный текст 		
			new_article_text.append(res)
		#получаем форматированный текст статьи
		self.article_text = new_article_text
		
	def get_article_text(self):
		"""
		Поиск текста статьи из страницы html.

		"""
		html = self.html
		#переменные начала и конца статьи
		#ищем начало статьи по тегу article
		article_start = html.find('</h1>')
		#ищем место завершения статьи по тегу article 
		article_end = max(html.rfind('/article'),html.rfind('articleBody')) 	
		
		#если тег завершения статьи не найден, то смотрим до конца страницы
		if article_end == 0:
			article_end = len(html)

		#срез страницы по границам статьи
		search_article_text = html[article_start:article_end]
		#создаем шаблон параграфов, где будем искать текст
		pattern_paragraph = r'(<p.+</p>)'
		#получаем список всех текстов по параграфам
		result = ''.join((re.findall(pattern_paragraph, search_article_text))).split('</p>')[:-1]
		#перебор текстов из списка текстов параграфов
		for s in result:
			#добавляем текст статьи
			self.article_text.append(s)
 
	def get_article_header(self):
		"""
		Поиска заголовка статьи
		"""
		html = self.html
		#находим начало заголовка 
		header_start = html.find('<h1')
		#находим конец заголовка
		header_end = html.rfind('</h1')
		#срез заголовка
		result = html[header_start:header_end]
		#оставляем только символы в заголовке
		result = re.sub(r'[^а-яА-Я]',' ',result) 
		#удаляем лишние пробелы 
		result = re.sub(r'\s+',' ',result)
		#формируем заголовок статьи
		self.article_header = result

	def save(self):
		"""
		Сохранение заголовка и статьи в файл 
		"""
		#формируем url
		url = urlparse(str(self.base_url))
		#имя и формат сохранения файла 
		filename = '{}{}.{}'.format(url.netloc, url.path[:-1], self.settings.get('file_format'))
		os.makedirs(os.path.dirname(filename), exist_ok=True)
		#сохранение файла
		with open(filename, "w") as f:
			f.write(self.article_header + '\n\n' + self.article_text_wrap) 

	def wrap(self):
		"""
		Форматирование текста с учетом настройки длины строки
		"""
		text = ''
		for s in self.article_text:
			dedented_text = textwrap.dedent(s)	
			text += textwrap.fill(dedented_text, width = self.settings.get('text_width')) + '\n'		
		self.article_text_wrap = text

if __name__ == '__main__':
	#Получение url из консоли
	BASE_URL = str(sys.argv[1])
	parser = myParser(BASE_URL)
	parser.get_html()
	parser.load()
	parser.get_article_header()
	parser.get_article_text()
	parser.get_links()
	parser.wrap()
	parser.save()
