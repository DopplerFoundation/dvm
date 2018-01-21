from cement.core.controller import CementBaseController, expose
from .login import AuthLoginController
from .register import AuthRegisterController
from utils.services.provider import ProviderService
from utils.services.wallet import WalletService


class AuthController(CementBaseController):
  class Meta:
    label = 'auth'
    stacked_on = 'base'
    stacked_type = 'nested'
    usage = 'dvm auth [command] [arguments...]'
    description = "User authentication and management"

  
  def _setup(self, app):
    super(AuthController, self)._setup(app)
    app.handler.register(AuthRegisterController)
    app.handler.register(AuthLoginController)


  @expose(hide=True)
  def default(self):
    self.app.args.print_help()
    
  
  @expose(help="Generate a DOP wallet")
  def generate_wallet(self):
    wallet = WalletService.generate()
    self.app.log.info("Wallet Address: " + wallet.address)
    self.app.log.info("Private Key: " + wallet.private_key)