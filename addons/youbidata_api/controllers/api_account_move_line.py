from odoo import http
from odoo.http import request
from datetime import datetime
import json


class AccountMoveLinesAPIController(http.Controller):

    @http.route(
        '/api/v1/account_move_lines',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    def get_account_move_lines(self, date_from=None, date_to=None, limit=None, offset=None, write_date_from=None, **kwargs):
        """
        API endpoint to retrieve account.move.line records

        Parameters:
            - date_from (optional): Start date in YYYY-MM-DD format
            - date_to (optional): End date in YYYY-MM-DD format
            - limit (optional): Number of records per page (default: 500)
            - offset (optional): Pagination offset (default: 0)
            - write_date_from (optional): Filter records with write_date >= this value
              Format: 'YYYY-MM-DD HH:MM:SS' (for incremental sync)

        Returns:
            JSON object with:
            - total_count: Total number of records matching the criteria
            - limit: Applied limit
            - offset: Applied offset
            - records: List of account.move.line records

        Note:
            Records are automatically filtered for company IDs 6 and 7.
            Records are ordered by write_date ASC, id ASC.
        """

        # Validate and parse date parameters
        dt_from = None
        dt_to = None

        if date_from:
            try:
                dt_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            except ValueError:
                return request.make_response(
                    json.dumps({'error': 'Il parametro "date_from" deve essere nel formato YYYY-MM-DD.'}, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')]
                )

        if date_to:
            try:
                dt_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                return request.make_response(
                    json.dumps({'error': 'Il parametro "date_to" deve essere nel formato YYYY-MM-DD.'}, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')]
                )

        # Validate date range logic
        if dt_from and dt_to and dt_from > dt_to:
            return request.make_response(
                json.dumps({'error': 'Il parametro "date_from" non può essere successivo a "date_to".'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )

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
        domain = [('parent_state', '=', 'posted')]

        # Add write_date filter for incremental sync
        if write_date_from:
            domain.append(('write_date', '>=', write_date_from))

        # Add company filter (fixed to IDs 6 and 7)
        domain.append(('company_id', 'in', company_id_list))

        # Add date filters if provided
        if dt_from:
            domain.append(('date', '>=', str(dt_from)))
        if dt_to:
            domain.append(('date', '<=', str(dt_to)))

        # Query data using sudo() for public access
        try:
            # Get total count of records matching the criteria
            total_count = request.env['account.move.line'].sudo().search_count(domain)

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
            lines = request.env['account.move.line'].sudo().search_read(
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