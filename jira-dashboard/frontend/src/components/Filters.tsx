import React from 'react';
import { Calendar, Filter, User, FolderOpen } from 'lucide-react';
import { Filters as FilterType } from '../types';

interface FiltersProps {
  filters: FilterType;
  onFiltersChange: (filters: FilterType) => void;
  projects?: Array<{ id: number; name: string; key?: string }>;
  users?: Array<{ id: number; display_name: string }>;
}

const Filters: React.FC<FiltersProps> = ({
  filters,
  onFiltersChange,
  projects = [],
  users = []
}) => {
  const handleInputChange = (field: keyof FilterType, value: string | number | undefined) => {
    onFiltersChange({
      ...filters,
      [field]: value || undefined
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Filter className="h-5 w-5 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Project Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <FolderOpen className="h-4 w-4 inline mr-1" />
            Project
          </label>
          <select
            value={filters.project_id || ''}
            onChange={(e) => handleInputChange('project_id', e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Projects</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}{project.key ? ` (${project.key})` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* User Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <User className="h-4 w-4 inline mr-1" />
            User
          </label>
          <select
            value={filters.user_id || ''}
            onChange={(e) => handleInputChange('user_id', e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Users</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.display_name}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={filters.status || ''}
            onChange={(e) => handleInputChange('status', e.target.value || undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="To Do">To Do</option>
            <option value="In Progress">In Progress</option>
            <option value="Code Review">Code Review</option>
            <option value="Testing">Testing</option>
            <option value="Done">Done</option>
          </select>
        </div>

        {/* Date Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Calendar className="h-4 w-4 inline mr-1" />
            Start Date
          </label>
          <input
            type="date"
            value={filters.start_date || ''}
            onChange={(e) => handleInputChange('start_date', e.target.value || undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Calendar className="h-4 w-4 inline mr-1" />
            End Date
          </label>
          <input
            type="date"
            value={filters.end_date || ''}
            onChange={(e) => handleInputChange('end_date', e.target.value || undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Quick Filter Buttons */}
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          onClick={() => onFiltersChange({})}
          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
        >
          Clear All
        </button>
        <button
          onClick={() => {
            const today = new Date();
            const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
            onFiltersChange({
              start_date: lastWeek.toISOString().split('T')[0],
              end_date: today.toISOString().split('T')[0]
            });
          }}
          className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
        >
          Last 7 Days
        </button>
        <button
          onClick={() => {
            const today = new Date();
            const lastMonth = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
            onFiltersChange({
              start_date: lastMonth.toISOString().split('T')[0],
              end_date: today.toISOString().split('T')[0]
            });
          }}
          className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
        >
          Last 30 Days
        </button>
      </div>
    </div>
  );
};

export default Filters;