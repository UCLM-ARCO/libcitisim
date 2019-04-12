using System;
using System.Diagnostics;
using System.Text;
using System.Threading;
using Xunit;

namespace LibCitisim
{

    public class PSService : IDisposable {
        private static PSService instance = null;
        private static readonly object safe = new object();

        private string pwd = Environment.GetEnvironmentVariable("TEST_DIR");
        private string config;
        private Process psServer;

        PSService() {
            Console.WriteLine("++++ called constructor of PS Service");
            config = pwd + "/tests.config";

            psServer = new Process();
            psServer.StartInfo.FileName = "property-server";
            psServer.StartInfo.Arguments = "--Ice.Config=" + config;
            psServer.StartInfo.WorkingDirectory = pwd;
            psServer.StartInfo.UseShellExecute = false;
            psServer.StartInfo.RedirectStandardError = true;
            psServer.StartInfo.RedirectStandardOutput = true;

            StringBuilder output = new StringBuilder();
            EventWaitHandle ev = new EventWaitHandle(false, EventResetMode.AutoReset);
            psServer.OutputDataReceived += new DataReceivedEventHandler((sender, e) => {
                if (!String.IsNullOrEmpty(e.Data)) {
                    output.Append(e.Data);
                    ev.Set();
                }
            });
            psServer.ErrorDataReceived += new DataReceivedEventHandler((sender, e) => {
                if (!String.IsNullOrEmpty(e.Data)) {
                    Console.WriteLine(e.Data);
                }
            });
            Assert.True(psServer.Start());
            psServer.BeginOutputReadLine();
            psServer.BeginErrorReadLine();

            ev.WaitOne(5000);
            if (psServer.HasExited) {
                Console.WriteLine(psServer.StandardError.ReadToEnd());
            }
            string expected = "PropertyServer -t -e 1.1:tcp -h";
            Assert.Equal(expected, output.ToString().Substring(0, expected.Length));
        }

        public void Dispose() {
            if (psServer == null)
                return;

            Console.WriteLine("---- killing PS service...");
            psServer.Kill();
            psServer.WaitForExit(5000);
        }

        public static void StopService() {
            lock (safe) {
                if (instance == null)
                    return;
                instance.Dispose();
            }
        }

        public static void StartService() {
            lock (safe) {
                if (instance != null)
                    return;
                instance = new PSService();
            }
        }
    }
}
