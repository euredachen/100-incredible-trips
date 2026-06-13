import React from 'react';
import { Link } from 'react-router-dom';
import StarRating from './StarRating';

const typeLabels = {
  adventure: '探险',
  cultural: '人文',
  nature: '自然',
  food: '美食',
  art: '艺术',
  wellness: '康养',
};

const difficultyLabels = {
  easy: '轻松',
  moderate: '中等',
  hard: '挑战',
};

export default function Card({ trip }) {
  return (
    <Link
      to={`/trips/${trip.id}`}
      className="group flex flex-col glass-card overflow-hidden w-full h-full"
      style={{ minHeight: '400px' }}
    >
      <div className="h-48 overflow-hidden shrink-0">
        <img
          src={trip.cover_image}
          alt={trip.title}
          className="w-full h-full object-cover transition-transform duration-500 ease-out
                     group-hover:scale-105"
          loading="lazy"
          onError={(e) => {
            e.target.src = `https://placehold.co/800x450/1a1a2e/888888?text=${encodeURIComponent(trip.destination)}`;
          }}
        />
      </div>

      <div className="p-6 flex flex-col flex-1">
        {/* 标签行 */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <span
            className="capsule text-xs font-medium"
            style={{
              backgroundColor: 'var(--accent-warm-light)',
              color: 'var(--accent-warm)',
            }}
          >
            {typeLabels[trip.experience_type] || trip.experience_type}
          </span>
          <span
            className="capsule text-xs"
            style={{
              backgroundColor: 'var(--accent-cool-light)',
              color: 'var(--color-text-secondary)',
            }}
          >
            {difficultyLabels[trip.difficulty] || trip.difficulty}
          </span>
          {trip.duration_hours && (
            <span className="text-xs ml-auto" style={{ color: 'var(--color-text-secondary)' }}>
              {trip.duration_hours >= 24
                ? `${Math.floor(trip.duration_hours / 24)}天${trip.duration_hours % 24 > 0 ? `${trip.duration_hours % 24}h` : ''}`
                : `${trip.duration_hours}h`}
            </span>
          )}
        </div>

        <h3
          className="font-semibold leading-tight mb-1.5 line-clamp-2"
          style={{ fontSize: '17px', color: 'var(--color-text)' }}
        >
          {trip.title}
        </h3>

        <p className="text-sm mb-2" style={{ color: 'var(--color-text-secondary)' }}>
          {trip.destination}，{trip.country}
        </p>

        <div className="flex items-center gap-2 mt-auto pt-3">
          <StarRating score={trip.uniqueness_score} size="sm" />
          <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            {trip.uniqueness_score}/10
          </span>

          <a
            href={`https://www.fliggy.com/search?q=${encodeURIComponent(trip.destination + ' ' + trip.country + ' 旅游')}`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="ml-auto text-xs px-2.5 py-1 rounded-full font-medium
                       transition-all duration-200 opacity-0 group-hover:opacity-100"
            style={{
              backgroundColor: 'var(--accent-warm-light)',
              color: 'var(--accent-warm)',
            }}
            title="在飞猪预订"
          >
            🎫 预订
          </a>
        </div>

        {trip.subtitle && (
          <div
            className="mt-3 pt-3 opacity-0 group-hover:opacity-100
                       translate-y-1 group-hover:translate-y-0
                       transition-all duration-300 ease-out"
            style={{ borderTop: `0.5px solid var(--color-border)` }}
          >
            <p
              className="text-sm leading-relaxed line-clamp-2"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              {trip.subtitle}
            </p>
          </div>
        )}
      </div>
    </Link>
  );
}
