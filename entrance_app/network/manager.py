"""
Менеджер сетей — логика сохранения и загрузки связей лифтов/лестниц.
"""

import json
import os
import uuid

NETWORK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'network_data.json')


class NetworkManager:
    """Управление сетями связанных лифтов и лестниц"""

    def __init__(self):
        self.networks = self._load()

    def _load(self):
        """Загрузить сети из файла"""
        try:
            with open(NETWORK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self):
        """Сохранить сети в файл"""
        with open(NETWORK_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.networks, f, ensure_ascii=False, indent=2)

    def get_building_networks(self, building_id):
        """Получить все сети корпуса"""
        return self.networks.get(building_id, {}).get('networks', [])

    def create_network(self, building_id, network_type, object_ids_with_floors):
        """
        Создать новую сеть

        Args:
            building_id: ID корпуса
            network_type: 'elevator' или 'stairs'
            object_ids_with_floors: список кортежей [(obj_id, floor), ...]

        Returns:
            network_id или None
        """
        if len(object_ids_with_floors) < 2:
            return None

        network = {
            'network_id': str(uuid.uuid4()),
            'type': network_type,
            'objects': [
                {'id': obj_id, 'floor': floor}
                for obj_id, floor in object_ids_with_floors
            ]
        }

        if building_id not in self.networks:
            self.networks[building_id] = {'networks': []}

        self.networks[building_id]['networks'].append(network)
        self.save()
        return network['network_id']

    def delete_network(self, building_id, network_index):
        """Удалить сеть по индексу"""
        if building_id in self.networks:
            networks = self.networks[building_id].get('networks', [])
            if 0 <= network_index < len(networks):
                networks.pop(network_index)
                self.networks[building_id]['networks'] = networks
                self.save()
                return True
        return False

    def get_object_networks(self, building_id, object_id):
        """Получить все сети, в которые входит объект"""
        networks = self.get_building_networks(building_id)
        result = []
        for idx, network in enumerate(networks):
            for obj in network.get('objects', []):
                if obj.get('id') == object_id:
                    result.append({
                        'index': idx,
                        'network_id': network['network_id'],
                        'type': network['type'],
                        'connected_ids': [o['id'] for o in network['objects'] if o['id'] != object_id]
                    })
        return result

    def get_connected_ids(self, building_id, object_id):
        """Получить список ID связанных объектов для данного объекта"""
        networks = self.get_object_networks(building_id, object_id)
        if networks:
            # Берём первую сеть (обычно одна)
            return networks[0]['connected_ids']
        return []

    def get_all_objects_in_network(self, building_id, network_index):
        """Получить все объекты в сети по индексу"""
        networks = self.get_building_networks(building_id)
        if 0 <= network_index < len(networks):
            return networks[network_index].get('objects', [])
        return []
