from __future__ import absolute_import
from cement.core.controller import CementBaseController, expose
from cli.utils.services.provider import ProviderService
from cli.utils.services.app import AppService
import cli.config as config
import requests, os, zipfile, subprocess, sys


class ProviderEnrollController(CementBaseController):
  class Meta:
    label = 'enroll'
    stacked_on = 'provider'
    stacked_type = 'nested'
    usage = 'dvm enroll [arguments...]'
    description = 'Enroll provider in app'
    arguments = [
      (['--app', '-a'], dict(action='store', help="App ID to enroll in", dest="app")),
      (['--versions', '-v'], dict(action='store', help="Number of versions back to download", default=config.apps_supported_versions, dest="versions")),
      (['--model', '-m'], dict(action='store', help="Specific model to download", dest="model"))
    ]
   
  
  @expose(hide=True)
  def default(self): 
    os.makedirs(config.app_store, exist_ok=True)
    app_id = self.app.pargs.app
       
    if not app_id:
      return self.app.log.error("Please provide an app id")
      
    app = AppService.fetch(app_id)
    if not app: return self.app.log.error("App id invalid")
    
    app_id = str(app.id)
    apps_store = self.app.store.get("apps", {})
    app_store = apps_store[app_id] if app_id in apps_store else {}
    
    # Enroll app
    models = self.enroll_app()
    if models is None: return
    
    if len(models) == 0:
      return self.app.log.warning("App does not have any models to download")
    
    self.app.log.info("Enrolled in app {}".format(app.slug))
    
    
    # Enroll models
    if self.app.pargs.model:
      model_id = int(self.app.pargs.model)
      model_found = False
      
      for model in models:
        if model.version == model_id:
          model_found = True
          self.enroll_model(model, app_store)
          
      if not model_found:
        return self.app.log.warning("Model {} was not found".format(model_id))
      
    else: 
      versions = int(self.app.pargs.versions)
  
      for model in models[0:versions]:
        self.enroll_model(model, app_store)
    
    # Finish
    apps_store[app_id] = app_store
    self.app.store.set("apps", apps_store)
    self.app.log.info("All models are downloaded and enrolled!")
  
  
  def enroll_app(self):
    return ProviderService.enroll_app(
      app_id = self.app.pargs.app,
      enroll = True
    )
    
    
  def enroll_model(self, model, app_store):
    # Download app
    response = requests.get(config.host + model.urls.raw, stream=True, allow_redirects=True, headers={
      "access-token": self.app.store.get("access-token")
    })
    response.raise_for_status()
    
    appFolder = os.path.join(config.app_store, str(model.app_id))
    os.makedirs(appFolder, exist_ok=True)
    
    zipfileName = "{}.zip".format(model.version)
    zipfilePath = os.path.join(appFolder, zipfileName)
    
    with open(zipfilePath, 'wb') as f:
      for block in response.iter_content(1024):
        if block: f.write(block) 
      f.close()
      
    # Unzip app
    folderPath = os.path.join(appFolder, str(model.version))
    os.makedirs(folderPath, exist_ok=True)
    
    zip_ref = zipfile.ZipFile(zipfilePath, 'r')
    zip_ref.extractall(folderPath)
    zip_ref.close()  
    os.remove(zipfilePath)
    
    app_store[model.version] = folderPath
    
    # Dependencies
    requirements_path = "{}/requirements.txt".format(folderPath)
    if os.path.isfile(requirements_path):
      cmd = "pip3 install --user -r {}".format(requirements_path)
      process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
      while True:
        output = process.stdout.readline()
        if output == '' or process.poll() is not None:
          break
        if output:
          print(output.strip().decode('ascii'))
    
    # Enroll model
    ProviderService.enroll_model(
      app_id = model.app_id,
      version = model.version,
      enroll = True
    )
    
    self.app.log.info("Downloaded and enrolled in model {}".format(model.version))
