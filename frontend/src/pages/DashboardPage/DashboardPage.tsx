/**
 * Admin Dashboard - Overview Page
 * Displays comprehensive system analytics and monitoring
 */

import { useEffect, useState } from 'react';
import { adminApi } from '@/services/api';
import styles from './DashboardPage.module.css';

interface SystemStats {
  collections_count: number;
  documents_count: number;
  forms_count: number;
  chunks_count: number;
  storage_status: string;
}

interface UsageAnalytics {
  period: string;
  total_queries: number;
  prev_period_queries: number;
  change_percent: number;
  daily_data: Array<{ date: string; count: number }>;
  top_collections: Array<{ collection: string; count: number }>;
  avg_confidence: number;
}

interface Query {
  id: string;
  query_text: string;
  collection: string | null;
  confidence: number;
  processing_time: number;
  created_at: string;
  session_id: string;
  conversation_turns: number;
}

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'unhealthy' | 'down';
  response_time: number;
  port: number;
  details: any;
}

export const DashboardPage = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [analytics, setAnalytics] = useState<UsageAnalytics | null>(null);
  const [recentQueries, setRecentQueries] = useState<Query[]>([]);
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [period, setPeriod] = useState<string>('7days');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAllData = async () => {
      try {
        setLoading(true);

        const [statsRes, analyticsRes, queriesRes, servicesRes] = await Promise.all([
          adminApi.get('/admin/system-stats'),
          adminApi.get(`/admin/usage-analytics?period=${period}`),
          adminApi.get('/admin/recent-queries?limit=5'),
          adminApi.get('/admin/services-health'),
        ]);

        setStats(statsRes.data);
        setAnalytics(analyticsRes.data);
        setRecentQueries(queriesRes.data.queries);
        setServices(servicesRes.data.services);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        setError('Không thể tải dữ liệu dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, [period]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;
    return date.toLocaleDateString('vi-VN');
  };

  if (loading) {
    return (
      <div className={styles.dashboard}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <p>Đang tải dữ liệu...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.dashboard}>
        <div className={styles.error}>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      <h1 className={styles.title}>Tổng quan hệ thống</h1>

      <div className={styles.cardsGrid}>
        {/* Card 1: System Stats */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Thống kê hệ thống</h2>
          <div className={styles.statsGrid}>
            <div className={styles.statItem}>
              <div className={styles.statIcon}>📁</div>
              <div className={styles.statValue}>{stats?.collections_count || 0}</div>
              <div className={styles.statLabel}>Bộ thủ tục</div>
            </div>
            <div className={styles.statItem}>
              <div className={styles.statIcon}>📄</div>
              <div className={styles.statValue}>{stats?.documents_count || 0}</div>
              <div className={styles.statLabel}>Văn bản</div>
            </div>
            <div className={styles.statItem}>
              <div className={styles.statIcon}>📋</div>
              <div className={styles.statValue}>{stats?.forms_count || 0}</div>
              <div className={styles.statLabel}>Biểu mẫu</div>
            </div>
            <div className={styles.statItem}>
              <div className={styles.statIcon}>🧩</div>
              <div className={styles.statValue}>{(stats?.chunks_count || 0).toLocaleString()}</div>
              <div className={styles.statLabel}>Chunks</div>
            </div>
          </div>
        </div>

        {/* Card 2: Usage Analytics */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Phân tích sử dụng</h2>
            <select
              className={styles.periodSelect}
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              <option value="today">Hôm nay</option>
              <option value="7days">7 ngày</option>
              <option value="30days">30 ngày</option>
              <option value="3months">3 tháng</option>
            </select>
          </div>

          <div className={styles.analyticsContent}>
            <div className={styles.mainMetric}>
              <div className={styles.metricValue}>{analytics?.total_queries || 0}</div>
              <div className={styles.metricLabel}>Tổng truy vấn</div>
            </div>

            {analytics && analytics.total_queries > 0 ? (
              <>
                <div className={styles.changeIndicator}>
                  <span
                    className={analytics.change_percent >= 0 ? styles.positive : styles.negative}
                  >
                    {analytics.change_percent >= 0 ? '↑' : '↓'} {Math.abs(analytics.change_percent)}
                    %
                  </span>
                  <span className={styles.changeLabel}>so với kỳ trước</span>
                </div>

                {analytics.top_collections.length > 0 && (
                  <div className={styles.topCollections}>
                    <div className={styles.subTitle}>Top bộ thủ tục</div>
                    {analytics.top_collections.slice(0, 3).map((col, idx) => (
                      <div key={idx} className={styles.collectionRow}>
                        <span className={styles.collectionName}>{col.collection}</span>
                        <span className={styles.collectionCount}>{col.count} truy vấn</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className={styles.avgConfidence}>
                  <span>Độ tin cậy TB: </span>
                  <strong>{analytics.avg_confidence.toFixed(2)}</strong>
                </div>
              </>
            ) : (
              <div className={styles.noData}>
                <p>Chưa có dữ liệu sử dụng</p>
                <small>Dữ liệu sẽ xuất hiện khi có truy vấn từ người dùng</small>
              </div>
            )}
          </div>
        </div>

        {/* Card 3: Recent Queries */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Truy vấn gần đây</h2>
          <div className={styles.queriesList}>
            {recentQueries.length > 0 ? (
              recentQueries.map((query) => (
                <div key={query.id} className={styles.queryItem}>
                  <div className={styles.queryHeader}>
                    <span className={styles.queryText}>
                      {query.query_text.substring(0, 80)}
                      {query.query_text.length > 80 ? '...' : ''}
                    </span>
                    <span className={styles.queryTime}>{formatDate(query.created_at)}</span>
                  </div>
                  <div className={styles.queryMeta}>
                    {query.collection && <span className={styles.badge}>{query.collection}</span>}
                    <span className={styles.confidence}>
                      Confidence: {query.confidence.toFixed(2)}
                    </span>
                    <span className={styles.processingTime}>{query.processing_time}ms</span>
                  </div>
                </div>
              ))
            ) : (
              <div className={styles.noData}>
                <p>Chưa có truy vấn nào</p>
                <small>
                  Danh sách truy vấn sẽ hiển thị khi người dùng bắt đầu sử dụng hệ thống
                </small>
              </div>
            )}
          </div>
        </div>

        {/* Card 4: Services Health */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Trạng thái Microservices</h2>
          <div className={styles.servicesList}>
            {services.map((service, idx) => (
              <div key={idx} className={styles.serviceItem}>
                <div className={styles.serviceInfo}>
                  <span className={styles.serviceName}>{service.name}</span>
                  <span className={styles.servicePort}>:{service.port}</span>
                </div>
                <div className={styles.serviceStatus}>
                  <span
                    className={`${styles.statusBadge} ${
                      service.status === 'healthy'
                        ? styles.healthy
                        : service.status === 'unhealthy'
                          ? styles.unhealthy
                          : styles.down
                    }`}
                  >
                    {service.status === 'healthy' ? '✅' : '❌'} {service.status}
                  </span>
                  {service.status === 'healthy' && (
                    <span className={styles.responseTime}>{service.response_time}ms</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
