from odoo import http
from odoo.http import request
from datetime import datetime
import json


class AccountAPIController(http.Controller):

    @http.route(
        '/api/v1/account',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    def get_account(self, limit=None, offset=None, write_date_from=None, **kwargs):
        """
        API endpoint to retrieve account.account records

        Parameters:
            - limit (optional): Number of records per page (default: 500)
            - offset (optional): Pagination offset (default: 0)
            - write_date_from (optional): Filter records with write_date >= this value
              Format: 'YYYY-MM-DD HH:MM:SS' (for incremental sync)

        Returns:
            JSON object with:
            - total_count: Total number of records matching the criteria
            - limit: Applied limit
            - offset: Applied offset
            - records: List of account.account records

        Note:
            Records are automatically filtered for company IDs 6 and 7.
            Records are ordered by write_date ASC, id ASC.
        """

        # Fixed company IDs filter
        company_id_list = [6, 7]

        # Validate and parse pagination parameters
        try:
            page_limit = int(limit) if limit else 500
            if page_limit <= 0:
                return request.make_response(
                    json.dumps({'error': 'Il parametro "limit" deve essere un numero positivo.'}, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')]
                )
        except ValueError:
            return request.make_response(
                json.dumps({'error': 'Il parametro "limit" deve essere un numero intero.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        try:
            page_offset = int(offset) if offset else 0
            if page_offset < 0:
                return request.make_response(
                    json.dumps({'error': 'Il parametro "offset" deve essere un numero non negativo.'}, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')]
                )
        except ValueError:
            return request.make_response(
                json.dumps({'error': 'Il parametro "offset" deve essere un numero intero.'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

        # Validate write_date_from parameter
        if write_date_from:
            try:
                datetime.strptime(write_date_from, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return request.make_response(
                    json.dumps({'error': 'Il parametro "write_date_from" deve essere nel formato "YYYY-MM-DD HH:MM:SS".'}, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')]
                )

        # Build domain filter
        domain = [('deprecated', '=', False)]

        # Add write_date filter for incremental sync
        if write_date_from:
            domain.append(('write_date', '>=', write_date_from))

        # Add company filter (fixed to IDs 6 and 7)
        domain.append(('company_id', 'in', company_id_list))

        # Query data using sudo() for public access
        try:
            # Get total count of records matching the criteria
            total_count = request.env['account.account'].sudo().search_count(domain)

            # Check if any records exist
            if total_count == 0:
                return request.make_response(
                    json.dumps({
                        'warning': 'Nessun record trovato con i criteri specificati.',
                        'total_count': 0,
                        'limit': page_limit,
                        'offset': page_offset,
                        'records': []
                    }, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json; charset=utf-8')]
                )

            # Get paginated records ordered by write_date and id ascending
            lines = request.env['account.account'].sudo().search_read(
                domain,
                fields=None,  # Return all fields
                order='write_date asc, id asc',
                limit=page_limit,
                offset=page_offset
            )

            # Build response with metadata
            result = {
                'total_count': total_count,
                'limit': page_limit,
                'offset': page_offset,
                'records': lines
            }

            # Return JSON response with proper encoding
            response_body = json.dumps(result, ensure_ascii=False, default=str)
            return request.make_response(
                response_body,
                headers=[('Content-Type', 'application/json; charset=utf-8')]
            )

        except Exception as e:
            # Handle any unexpected errors
            return request.make_response(
                json.dumps({'error': f'Errore durante il recupero dei dati: {str(e)}'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )