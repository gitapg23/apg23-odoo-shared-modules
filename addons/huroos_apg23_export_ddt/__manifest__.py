# Copyright 2023 - Huroos srl - www.huroos.com
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html)

{
    'name': "Huroos | APG23 | Export DDT",
    'summary': """Modulo APG3 Export DDT""",
    'description': """Modulo APG23 Export DDT""",
    'author': "Huroos - www.huroos.com",
    'website': "www.huroos.com",
    'category': 'General',
    'license': 'LGPL-3',
    'version': '17.32',
    'depends': [
        'base',
        'huroos_ddt',
        'sh_product_customer_code',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/huroos_ddt.xml',
        'views/huroos_ddt_txt.xml',
        'views/res_config_settings.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'wizards/wizard_export_txt.xml',
    ]
}
