import { useQuery } from '@tanstack/react-query';
import { mockClient } from '../api/mockClient';

export const useAuditTrail = () =>
  useQuery({
    queryKey: ['audit-trail'],
    queryFn: () => mockClient.getAuditTrail()
  });
