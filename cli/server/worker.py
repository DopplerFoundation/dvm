from __future__ import absolute_import
from cli.utils.models.task import Task
from cli.utils.services.task import TaskService
from threading import Thread
import json, importlib.util, requests


class Worker():
  
  queue = None
  store = None
  interfaces = None
  

  def __init__(self, queue, store):
    self.queue = queue
    self.store = store
    self.loadInterfaces()
    
  
  def loadInterfaces(self):
    self.interfaces = self.store.get("apps")
    
    for app, models in self.interfaces.items():    
      for model, path in models.items():
        json_data=open("{}/package.json".format(path)).read()
        package_json = json.loads(json_data)
        spec = importlib.util.spec_from_file_location("{}.{}".format(app, model), "{}/{}".format(path, package_json["main"]))
        interface = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(interface)
        self.interfaces[app][model] = interface.ModelInterface()


  def start(self):
    thread = Thread(target=self.worker)
    thread.daemon = True
    thread.start()


  def worker(self):
    while True:
      input = self.queue.get()
      if input is not None:
        task = Task.build(input)
        self.task(task)
      self.queue.task_done()
      
      
  def predict(self, task):
    app_id = str(task.app_id)
    model_id = str(task.model_id)
    interface = self.interfaces[app_id][model_id]
    return interface.prediction(task.input)
  

  def task(self, task):
    try:      
      TaskService.send(
        method = task.callbacks.success.method,
        endpoint = task.callbacks.success.url,
        output = self.predict(task)
      )
    
    except Exception as e:      
      TaskService.error(
        method = task.callbacks.error.method,
        endpoint = task.callbacks.error.url,
        message = str(e)
      )
