'use client';

import Image from "next/image";
import { useQuery } from "@tanstack/react-query";

import { getAllSeries } from "@/lib/api/home";

export default function Home() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['series'],
    queryFn: () => getAllSeries(),
  });

  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-[32px] row-start-2 items-center w-full max-w-7xl">
        <h1 className="text-3xl font-bold">Title Card Maker</h1>
        
        {isLoading ? (
          <div className="text-center">Loading series...</div>
        ) : error ? (
          <div className="text-center text-red-500">Error loading series: {error.message}</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 w-full">
            {data?.items.map((item) => (
              <div 
                key={item.id} 
                className="flex flex-col items-center p-4 rounded-lg border border-gray-200 dark:border-gray-800 hover:shadow-lg transition-shadow"
              >
                {item.poster_url && (
                  <Image
                    src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4242'}${item.poster_url}`}
                    alt={`${item.name} poster`}
                    width={200}
                    height={300}
                    className="rounded-lg mb-4"
                  />
                )}
                <h2 className="text-lg font-semibold text-center">{item.name}</h2>
                {item.year && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">{item.year}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/file.svg"
            alt="File icon"
            width={16}
            height={16}
          />
          Learn
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/window.svg"
            alt="Window icon"
            width={16}
            height={16}
          />
          Examples
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/globe.svg"
            alt="Globe icon"
            width={16}
            height={16}
          />
          Go to nextjs.org →
        </a>
      </footer>
    </div>
  );
}
