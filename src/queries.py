FETCH_PROFILES = """SELECT * FROM public.profile"""
FETCH_ALL_PROFILE_TRANSACIONS = """SELECT * FROM public.asset_transactions
                                   WHERE user_id = %s"""
FETCH_ALL_ASSET_DATA = """SELECT FROM public.asset_data
                          WHERE asset_isin = %s"""
FETCH_ALL_ASSET_TYPES = """SELECT asset_type.id, asset_type.name
                            FROM asset_type 
                            ORDER BY asset_type.id"""
FETCH_ASSET_TYPE_BY_ASSET_TYPE_NAME = """SELECT asset_type.id
                                            FROM asset_type
                                            WHERE asset_type.name = %(asset_name)s
                                            ORDER BY asset_type.id"""
FETCH_PROFILE_ASSET_TRANSACTIONS_BY_USER_ID = """ SELECT
                                                    asset_transaction.user_id,
                                                    asset_transaction.asset_isin,
                                                    asset_transaction.quantity,
                                                    asset_transaction.price,
                                                    asset_transaction.date
                                                    FROM public.asset_transaction AS asset_transaction
                                                    INNER JOIN public.profile AS profile
                                                        ON asset_transaction.user_id = profile.id
                                                    WHERE asset_transaction.user_id = %(user_id)s
                                                    ORDER BY asset_transaction.date DESC
                                              """
FETCH_ASSET_DATA_BY_ASSET_ISIN = """SELECT 
                                        asset_data.asset_isin,
                                        asset_data.date,
                                        asset_data.mid_close,
                                        asset_data.high,
                                        asset_data.low,
                                        FROM public.asset_data as asset_data
                                        INNER JOIN public.asset as asset
                                            ON asset_data.asset_isin = asset.isin
                                        WHERE asset_data.asset_isin = %(asset_isin)s
                                        ORDER BY asset_data.date DESC
                                 """


FETCH_ASSET_TYPES_BY_PROFILE = """WITH user_assets AS (
                                  SELECT DISTINCT asset_type_id
                                  FROM asset 
                                  INNER JOIN asset_transaction
                                    ON asset.isin = asset_transaction.asset_isin
                                   WHERE asset_transaction.user_id = %(user_id)s)
                                   SELECT asset_type.id, asset_type.name
                                   FROM asset_type
                                   INNER JOIN user_assets
                                        ON asset_type.id = user_assets.asset_type_id
                                    ORDER BY asset_type_id"""
