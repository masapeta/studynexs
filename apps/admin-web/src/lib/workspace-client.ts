import { api } from "@/lib/api";
import type { WorkspaceResponse, WorkspaceTurnRequest } from "@/lib/workspace-types";

type WorkspaceTurnEnvelope = {
  data: WorkspaceResponse;
};

export async function createWorkspaceTurn(
  payload: WorkspaceTurnRequest
): Promise<WorkspaceResponse> {
  const response = await api<WorkspaceTurnEnvelope>("/api/v1/workspace/turn", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.data;
}