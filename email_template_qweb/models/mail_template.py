# Copyright 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models, tools


class MailTemplate(models.Model):
    _inherit = "mail.template"

    body_type = fields.Selection(
        [("qweb", "QWeb"), ("qweb_view", "QWeb View")],
        "Body templating engine",
        default="qweb",
        required=True,
    )
    body_view_id = fields.Many2one("ir.ui.view", domain=[("type", "=", "qweb")])
    body_view_arch = fields.Text(related="body_view_id.arch")

    def _generate_template(self, res_ids, render_fields):
        multi_mode = True
        IrQweb = self.env["ir.qweb"]

        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False
        result = super()._generate_template(res_ids, render_fields=render_fields)
        for lang, (_template, _template_res_ids) in self._classify_per_lang(
            res_ids
        ).items():
            self_with_lang = self.with_context(lang=lang)
            for res_id in res_ids:
                if self.body_type == "qweb_view" and (
                    not render_fields or "body_html" in render_fields
                ):
                    for record in self_with_lang.env[self.model].browse(res_id):
                        body_html = IrQweb._render(
                            self_with_lang.body_view_id.id,
                            {"object": record, "email_template": self_with_lang},
                        )
                        # Some wizards, like when sending a sales order, need this
                        # fix to display accents correctly
                        body_html = tools.exception_to_unicode(body_html)
                        result[res_id][
                            "body_html"
                        ] = self_with_lang._render_template_postprocess(
                            False, {res_id: body_html}
                        )[res_id]
                        result[res_id]["body"] = tools.html_sanitize(
                            result[res_id]["body_html"]
                        )
        return result if multi_mode else result[res_ids[0]]
