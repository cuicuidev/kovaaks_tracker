const std = @import("std");
const mem = std.mem;
const http = std.http;

pub fn sendPayload(allocator: mem.Allocator, payload: []const u8, endpoint: []const u8, jwt: []const u8) !void {
    var client = http.Client{ .allocator = allocator };
    defer client.deinit();

    const uri = try std.Uri.parse(endpoint);

    var buf: [1024]u8 = undefined;
    var req = try client.open(.POST, uri, .{ .server_header_buffer = &buf });
    defer req.deinit();

    var auth_header_buffer: [256]u8 = undefined;
    const auth_header_slice = try std.fmt.bufPrint(&auth_header_buffer, "Bearer {s}", .{jwt});
    req.headers.authorization = http.Client.Request.Headers.Value{ .override = auth_header_slice };

    req.transfer_encoding = .{ .content_length = payload.len };
    try req.send();
    var wtr = req.writer();
    try wtr.writeAll(payload);
    try req.finish();
    try req.wait();

    var rdr = req.reader();
    const body = try rdr.readAllAlloc(allocator, 1024 * 1024 * 4);
    defer allocator.free(body);
}

pub fn getLatest(allocator: mem.Allocator, endpoint: []const u8, jwt: []const u8) !i128 {
    var client = http.Client{ .allocator = allocator };
    defer client.deinit();

    const uri = try std.Uri.parse(endpoint);

    var buf: [1024]u8 = undefined;
    var req = try client.open(.GET, uri, .{ .server_header_buffer = &buf });
    defer req.deinit();

    var auth_header_buffer: [256]u8 = undefined;
    const auth_header_slice = try std.fmt.bufPrint(&auth_header_buffer, "Bearer {s}", .{jwt});
    req.headers.authorization = http.Client.Request.Headers.Value{ .override = auth_header_slice };

    try req.send();
    try req.finish();
    try req.wait();

    var rdr = req.reader();
    const body = try rdr.readAllAlloc(allocator, 1024 * 1024 * 4);
    defer allocator.free(body);
    return std.fmt.parseInt(i128, body, 10);
}
