from odoo import fields, models, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    access_users_ids = fields.Many2many('res.users', 'rel_pos_config_res_users', 'pos_config_id','res_user_id',
                                      string='POS Access')
    structure_id = fields.Many2one("onlus.struttura", string="Struttura")

    def _get_available_product_domain(self):
        domain = super()._get_available_product_domain()
        domain.append(('pos_ids', 'in', self.ids))
        return domain



    # def _force_http(self):
    #     return True
    #
    # def _action_to_open_ui(self):
    #     if not self.current_session_id:
    #         self.env['pos.session'].create({'user_id': self.env.uid, 'config_id': self.id})
    #     path = '/pos/web'
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': path + '?config_id=%d' % self.id,
    #         'target': 'self',
    #     }
