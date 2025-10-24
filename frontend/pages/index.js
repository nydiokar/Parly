import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function Home() {
  const [data, setData] = useState(null);
  const [dataWithBudget, setDataWithBudget] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      fetch('/api/votes/stats/day-of-week?exclude_budget_votes=true'),
      fetch('/api/votes/stats/day-of-week?exclude_budget_votes=false')
    ])
      .then(([res1, res2]) => Promise.all([res1.json(), res2.json()]))
      .then(([data1, data2]) => {
        setData(data1); // Excluding budget votes
        setDataWithBudget(data2); // Including budget votes
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  if (error) return <div className="min-h-screen flex items-center justify-center text-red-500">Error: {error}</div>;

  // Prepare data for the chart
  const chartData = [
    { day: 'Mon', votes: data.day_counts.Monday, percentage: data.day_percentages.Monday },
    { day: 'Tue', votes: data.day_counts.Tuesday, percentage: data.day_percentages.Tuesday },
    { day: 'Wed', votes: data.day_counts.Wednesday, percentage: data.day_percentages.Wednesday },
    { day: 'Thu', votes: data.day_counts.Thursday, percentage: data.day_percentages.Thursday },
    { day: 'Fri', votes: data.day_counts.Friday, percentage: data.day_percentages.Friday },
    { day: 'Sat', votes: data.day_counts.Saturday, percentage: data.day_percentages.Saturday },
    { day: 'Sun', votes: data.day_counts.Sunday, percentage: data.day_percentages.Sunday },
  ];

  const weekDays = chartData.slice(0, 5); // Mon-Fri
  const weekends = chartData.slice(5); // Sat-Sun

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Canadian Parliament Data
          </h1>
          <p className="text-xl text-gray-600">
            Exploring patterns in parliamentary democracy
          </p>
        </header>

        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
            The 4-Day Work Week
          </h2>

          <div className="text-center mb-8">
            <p className="text-lg text-gray-700 mb-4">
              When does Parliament work? Analysis of parliamentary voting patterns.
            </p>

            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-blue-800 mb-2">Excluding Budget Votes</h3>
                <p className="text-2xl font-bold text-blue-700">
                  {data.monday_to_thursday_percentage}% Mon-Thu
                </p>
                <p className="text-sm text-blue-600 mt-1">
                  {data.total_vote_events.toLocaleString()} votes, {data.total_days_with_votes} days
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-green-800 mb-2">Including Budget Votes</h3>
                <p className="text-2xl font-bold text-green-700">
                  {dataWithBudget.monday_to_thursday_percentage}% Mon-Thu
                </p>
                <p className="text-sm text-green-600 mt-1">
                  {dataWithBudget.total_vote_events.toLocaleString()} votes, {dataWithBudget.total_days_with_votes} days
                </p>
              </div>
            </div>

            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
              <p className="text-yellow-800 font-medium">
                ⚠️ <strong>Data Transparency:</strong> We show both versions to avoid misleading conclusions.
              </p>
              <p className="text-yellow-700 text-sm mt-2">
                Budget votes are routine government spending approvals that may follow different scheduling patterns.
                Excluding them provides insight into policy-focused parliamentary work.
              </p>
            </div>
          </div>

          <div className="mb-8">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip
                  formatter={(value, name, props) => [
                    `${value.toLocaleString()} votes (${props.payload.percentage}%)`,
                    'Votes'
                  ]}
                />
                <Bar
                  dataKey="votes"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-green-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold text-green-800 mb-3">
                🏛️ Work Week (Mon-Thu)
              </h3>
              <p className="text-sm text-green-600 mb-3">Excluding budget votes</p>
              <div className="space-y-2">
                {weekDays.map(day => (
                  <div key={day.day} className="flex justify-between">
                    <span className="font-medium">{day.day}:</span>
                    <span>{day.votes.toLocaleString()} votes ({day.percentage}%)</span>
                  </div>
                ))}
                <div className="border-t pt-2 mt-3">
                  <div className="flex justify-between font-semibold text-green-800">
                    <span>Total:</span>
                    <span>{data.monday_to_thursday_percentage}% of policy votes</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold text-gray-800 mb-3">
                🏖️ Weekends (Fri-Sun)
              </h3>
              <p className="text-sm text-gray-600 mb-3">Excluding budget votes</p>
              <div className="space-y-2">
                {weekends.map(day => (
                  <div key={day.day} className="flex justify-between">
                    <span className="font-medium">{day.day}:</span>
                    <span>{day.votes.toLocaleString()} votes ({day.percentage}%)</span>
                  </div>
                ))}
                <div className="border-t pt-2 mt-3">
                  <div className="flex justify-between font-semibold text-gray-800">
                    <span>Total:</span>
                    <span>{(100 - data.monday_to_thursday_percentage).toFixed(1)}% of policy votes</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 text-center text-sm text-gray-500">
            <p>
              Primary analysis excludes budget votes to focus on policy debates •
              We show both versions for transparency •
              Analysis covers 32 years of parliamentary voting data (1993-2025)
            </p>
          </div>
        </div>

        <footer className="text-center text-gray-500">
          <p>Built with Next.js, Recharts, and Tailwind CSS</p>
        </footer>
      </div>
    </div>
  );
}
