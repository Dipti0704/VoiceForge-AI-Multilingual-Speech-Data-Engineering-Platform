/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#182027",
        panel: "#f7f8fa",
        line: "#d9dee4",
        signal: "#167c80",
        warn: "#b86b00",
        danger: "#bb2d3b"
      }
    }
  },
  plugins: []
};

