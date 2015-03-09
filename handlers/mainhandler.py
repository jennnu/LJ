import jinja2
import os
import tornado.ioloop
import tornado.web

template_dir = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class MainHandler(tornado.web.RequestHandler):

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def get_current_user(self):
		return self.get_secure_cookie('email')