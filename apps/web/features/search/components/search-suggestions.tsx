"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchSearchSuggestions } from "../suggestions-api";

interface SearchSuggestionsProps {
  query: string;
  onQueryChange: (value: string) => void;
  onSelect: (value: string) => void;
  inputId: string;
}

export function SearchSuggestions({
  query,
  onQueryChange,
  onSelect,
  inputId,
}: SearchSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch suggestions with debounce
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (query.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      const results = await fetchSearchSuggestions(query);
      setSuggestions(results);
      setIsOpen(results.length > 0);
      setActiveIndex(-1);
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query]);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = useCallback(
    (value: string) => {
      onSelect(value);
      setIsOpen(false);
      setActiveIndex(-1);
    },
    [onSelect]
  );

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (!isOpen || suggestions.length === 0) return;

      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          setActiveIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : prev));
          break;
        case "ArrowUp":
          event.preventDefault();
          setActiveIndex((prev) => (prev > 0 ? prev - 1 : -1));
          break;
        case "Enter":
          if (activeIndex >= 0 && suggestions[activeIndex]) {
            event.preventDefault();
            handleSelect(suggestions[activeIndex]);
          }
          break;
        case "Escape":
          setIsOpen(false);
          setActiveIndex(-1);
          break;
      }
    },
    [isOpen, suggestions, activeIndex, handleSelect]
  );

  return (
    <div ref={containerRef} className="relative w-full">
      <input
        id={inputId}
        type="text"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => suggestions.length > 0 && setIsOpen(true)}
        className="w-full rounded-md border border-border-strong bg-surface px-3 h-11 text-content placeholder:text-content-muted"
        placeholder="e.g. recurring headaches with nausea"
        autoComplete="off"
        aria-autocomplete="list"
        aria-expanded={isOpen}
        aria-controls={`${inputId}-suggestions`}
        aria-activedescendant={
          activeIndex >= 0 ? `${inputId}-suggestion-${activeIndex}` : undefined
        }
      />
      <p className="mt-1.5 text-sm text-content-muted">
        Describe a presentation in plain language (max 500 characters).
      </p>

      {isOpen && suggestions.length > 0 && (
        <ul
          id={`${inputId}-suggestions`}
          role="listbox"
          className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md border border-border-strong bg-surface shadow-lg"
        >
          {suggestions.map((suggestion, index) => (
            <li
              key={suggestion}
              id={`${inputId}-suggestion-${index}`}
              role="option"
              aria-selected={activeIndex === index}
              onClick={() => handleSelect(suggestion)}
              onMouseEnter={() => setActiveIndex(index)}
              className={`cursor-pointer px-3 py-2 text-sm ${
                activeIndex === index
                  ? "bg-accent-surface text-accent"
                  : "text-content-secondary hover:bg-surface-raised"
              }`}
            >
              {suggestion}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
