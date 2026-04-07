import axios from "axios";
import type { Building, Floor, Room, Technical, Entrance, PathResponse } from "./types";

const api = axios.create({
  baseURL: "",
});

export const fetchBuildings = async (): Promise<Building[]> => {
  const { data } = await api.get<Building[]>("/buildings");
  return data;
};

export const fetchFloors = async (buildingId: string): Promise<Floor[]> => {
  const { data } = await api.get<Floor[]>(`/buildings/${buildingId}/floors`);
  return data;
};

export const fetchRooms = async (
  buildingId: string,
  floorNumber: string
): Promise<Room[]> => {
  const { data } = await api.get<Room[]>(
    `/buildings/${buildingId}/floors/${floorNumber}/rooms`
  );
  return data;
};

export const fetchTechnical = async (
  buildingId: string,
  floorNumber: string
): Promise<Technical[]> => {
  const { data } = await api.get<Technical[]>(
    `/buildings/${buildingId}/floors/${floorNumber}/technical`
  );
  return data;
};

export const fetchEntrances = async (
  buildingId: string,
  floorNumber: string
): Promise<Entrance[]> => {
  const { data } = await api.get<Entrance[]>(
    `/buildings/${buildingId}/floors/${floorNumber}/entrances`
  );
  return data;
};

export const findPath = async (
  buildingId: string,
  startObjectId: string,
  endObjectId: string
): Promise<PathResponse> => {
  const { data } = await api.post<PathResponse>("/path", {
    building_id: buildingId,
    start_object_id: startObjectId,
    end_object_id: endObjectId,
  });
  return data;
};
