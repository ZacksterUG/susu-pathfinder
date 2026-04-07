-- Триггер для автоматического обновления updated_at в таблице grid

CREATE OR REPLACE FUNCTION map_app.update_updated_at_column()
RETURNS TRIGGER AS '
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;' LANGUAGE plpgsql;

CREATE TRIGGER update_grid_updated_at
    BEFORE UPDATE ON map_app.grid
    FOR EACH ROW
    EXECUTE FUNCTION map_app.update_updated_at_column();
