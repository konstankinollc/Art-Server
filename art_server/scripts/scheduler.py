"""
A simple task scheduling script which schedules tasks defined in settings.SCHEDULED_TASKS.
Copied wholesale from http://code.activestate.com/recipes/114644/ then tweaked for Django
"""
import time
import threading
import readline
import cmd

class Task(threading.Thread):
	def __init__(self, action, loopdelay, initdelay):
		self._action = action
		self._loopdelay = loopdelay
		self._initdelay = initdelay
		self._running = 1
		threading.Thread.__init__(self)

	def run(self):
		if self._initdelay:
			time.sleep(self._initdelay)
		self._runtime = time.time()
		while self._running:
			start = time.time()
			self._action()
			self._runtime += self._loopdelay
			time.sleep(max(0, self._runtime - start))
	
	def stop(self):
		self._running = 0

class TestTask(Task):
	def __init__(self, loopdelay, initdelay, name="TestTask"):
		self.name = name
		Task.__init__(self, self.do_it, loopdelay, initdelay)
	def do_it(self):
		print 'Doing it: %s' % self.name

class Scheduler:
	def __init__(self):
		self._tasks = []
	
	def __repr__(self):
		rep = ''
		for task in self._tasks:
			rep += '%s\n' % `task`
		return rep
	
	def add_task(self, task):
		self._tasks.append(task)
	
	def start_all_tasks(self):
		for task in self._tasks:
			task.start()
	
	def stop_all_tasks(self):
		for task in self._tasks:
			print 'Stopping task', task
			task.stop()
			task.join()
			print 'Stopped'

class Console(cmd.Cmd):
	def do_it(self, args):
		print 'doing it'
	def default(self, line):
		print 'line %s' % line

if __name__ == '__main__':
	import settings
	import sys
	s = Scheduler()
	for task in settings.SCHEDULED_TASKS: s.add_task(task)
	s.start_all_tasks()