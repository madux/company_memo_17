# -*- coding: utf-8 -*-
import base64
import json
import logging
import random
from multiprocessing.spawn import prepare
import urllib.parse
from odoo import http, fields
from odoo.exceptions import ValidationError
from odoo.tools import consteq, plaintext2html
from odoo.http import request
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import odoo
import odoo.addons.web.controllers.home as main
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url, is_user_internal
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)
# Shared parameters for all login/signup flows


class OfficeDashboard(http.Controller):
	
	@http.route(["/office-dashboard"], type='http', auth='user', website=True, website_published=True)
	def office_dashboard(self):
		vals = {
			"memo_ids": request.env["memo.model"].sudo().search([]),
		}
		return request.render("maach_dashboard.maach_dashboard_template_id", vals)
	
	@http.route(["/memo-records"], type='http', auth='user', website=True, website_published=True)
	def open_related_record_view(self):
		url = "/web#action=487&model=memo.model&view_type=list&cids=1&menu_id=333"
		return request.redirect(url)