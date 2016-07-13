# -*- coding: utf-8 -*-
import requests
import Queue
import threading
import sys
import os

counter = 0
lock = threading.Semaphore()
shared_lock = threading.Lock()
queue = Queue.Queue()
websites = {'wordpress' : [], 'joomla' : [], 'other' : []}

def check_cms(url):
	res = requests.get(url, timeout=20)
	if res.status_code == 200:
		try:
			key = 'other'
			shared_lock.acquire()
			if 'wp-include' in res.content:
				key = 'wordpress'
			elif 'joomla' in res.content:
				key = 'joomla'

			websites[key].append(url)
		finally:
			shared_lock.release()

def thread_proc():
	while True:
		if queue.empty():
			break

		url = queue.get()
		try:
			try:
				lock.acquire()
				print '[+] Scan website %s' % url
			finally:
				lock.release()
			
			check_cms(url)
		except Exception as e:
			print e

		queue.task_done()

def save_result(id):
	dirs = os.path.join('output', id)
	if not os.path.exists(dirs):
		os.makedirs(dirs)

	for cms_name, urls in websites.items():
		if len(urls) == 0:
			continue

		fname = os.path.join(dirs, cms_name + '.txt')
		with open(fname, 'w+') as handle:
			for url in urls:
				handle.write(url + '\n')

def main():
	global counter
	thread_pool = []

	if len(sys.argv) < 2:
		print 'Usage: sitefilter.py <urls-file> [--save]'
		return

	with open(sys.argv[1], 'r') as handle:
		for url in handle:
			if url.find('http://'):
				url = 'http://' + url
			queue.put(url.replace('\n', ''))

			counter += 1

	print 'Totally %d webiste(s) load' % counter

	for i in range(10):
		t = threading.Thread(target=thread_proc)
		t.setDaemon(True)
		t.start()

		thread_pool.append(t)

	for t in thread_pool:
		t.join()

	for cms_name, urls in websites.items():
		print '[%s]' % cms_name
		for url in urls:
			print url


	if len(sys.argv) > 2 and (sys.argv[2] == '-s' or sys.argv[2] == '--save'):
		save_result(sys.argv[1].replace('.', '_'))

if __name__ == '__main__':
	main()