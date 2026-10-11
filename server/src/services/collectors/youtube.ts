import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

export class YouTubeCollector {
  private apiKey: string;

  constructor() {
    this.apiKey = process.env.YOUTUBE_API_KEY || '';
  }

  async searchVideos(
    query: string,
    maxResults: number = 10
  ): Promise<any[]> {
    if (!this.apiKey) {
      throw new Error('YouTube API key not configured');
    }

    try {
      const response = await axios.get(
        'https://www.googleapis.com/youtube/v3/search',
        {
          params: {
            part: 'snippet',
            q: query,
            type: 'video',
            order: 'date',
            maxResults,
            key: this.apiKey,
          },
        }
      );

      return response.data.items.map((item: any) => ({
        platform: 'youtube',
        title: item.snippet.title,
        url: `https://youtube.com/watch?v=${item.id.videoId}`,
        author: item.snippet.channelTitle,
        score: 0, // YouTube search doesn't provide view counts
        excerpt: item.snippet.description.substring(0, 500),
        metadata: {
          videoId: item.id.videoId,
          channelId: item.snippet.channelId,
          publishedAt: item.snippet.publishedAt,
          thumbnail: item.snippet.thumbnails?.high?.url,
        },
      }));
    } catch (error) {
      console.error('YouTube search failed:', error);
      throw new Error('Failed to search YouTube');
    }
  }

  async getVideoDetails(videoIds: string[]): Promise<any[]> {
    if (!this.apiKey || videoIds.length === 0) {
      return [];
    }

    try {
      const response = await axios.get(
        'https://www.googleapis.com/youtube/v3/videos',
        {
          params: {
            part: 'snippet,statistics',
            id: videoIds.join(','),
            key: this.apiKey,
          },
        }
      );

      return response.data.items.map((item: any) => ({
        videoId: item.id,
        viewCount: parseInt(item.statistics.viewCount || '0'),
        likeCount: parseInt(item.statistics.likeCount || '0'),
        commentCount: parseInt(item.statistics.commentCount || '0'),
      }));
    } catch (error) {
      console.error('Failed to get video details:', error);
      return [];
    }
  }
}

export const youtubeCollector = new YouTubeCollector();
