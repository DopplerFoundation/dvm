from __future__ import absolute_import
from cli.utils.services import *
from cli.utils.models.app import App

class AppService(BaseService):
  
  @classmethod
  def fetch(cls, app_id):    
    request = Request(
      method = "get",
      authenticated = True,
      endpoint = "/v1/apps/{}".format(app_id),
    )
    
    response = cls.request(request)
    if not response: return 
    return App.build(response["app"])