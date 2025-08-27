from click.testing import CliRunner
from eduschedule.cli.main import app

def cliCommandTest(cliEnv):
    runner = CliRunner()
    res = runner.invoke(app, ['db-init'], env=cliEnv)