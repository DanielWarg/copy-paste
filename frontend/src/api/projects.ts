/**
 * Projects API
 * 
 * API layer for project management.
 * All functions use the centralized api client with request correlation.
 */

import { apiRequest } from './client';

export interface Project {
  id: number;
  name: string;
  sensitivity: 'standard' | 'sensitive';
  status: 'active' | 'archived';
  created_at: string;
  updated_at: string;
  started_working_at?: string;
  start_date?: string; // ISO date string (YYYY-MM-DD)
  due_date?: string; // ISO date string (YYYY-MM-DD)
  transcripts_count: number;
  notes_count: number;
  files_count: number;
  last_activity_at?: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateProjectRequest {
  name: string;
  start_date?: string; // ISO date string (YYYY-MM-DD)
  due_date?: string; // ISO date string (YYYY-MM-DD)
  sensitivity?: 'standard' | 'sensitive';
}

export interface UpdateProjectRequest {
  name?: string;
  start_date?: string;
  due_date?: string;
  sensitivity?: 'standard' | 'sensitive';
  status?: 'active' | 'archived';
}

export interface CreateProjectResponse extends Project {}

/**
 * List all projects
 */
export async function listProjects(params?: {
  q?: string;
  status?: string;
  sensitivity?: string;
  limit?: number;
  offset?: number;
}): Promise<ProjectListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.q) queryParams.append('q', params.q);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.sensitivity) queryParams.append('sensitivity', params.sensitivity);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  const url = `/api/v1/projects${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  return apiRequest<ProjectListResponse>(url, {
    method: 'GET',
  });
}

/**
 * Create a new project
 */
export async function createProject(data: CreateProjectRequest): Promise<CreateProjectResponse> {
  return apiRequest<CreateProjectResponse>('/api/v1/projects', {
    method: 'POST',
    body: {
      name: data.name,
      start_date: data.start_date,
      due_date: data.due_date,
      sensitivity: data.sensitivity || 'standard',
    },
  });
}

/**
 * Update an existing project
 */
export async function updateProject(
  projectId: number,
  data: UpdateProjectRequest
): Promise<Project> {
  return apiRequest<Project>(`/api/v1/projects/${projectId}`, {
    method: 'PUT',
    body: data,
  });
}

/**
 * Get project by ID
 */
export async function getProject(projectId: number): Promise<Project> {
  return apiRequest<Project>(`/api/v1/projects/${projectId}`, {
    method: 'GET',
  });
}

